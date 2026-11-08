from __future__ import annotations

import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Course, Document, DocumentChunk, KnowledgePoint
from .selectors import courses_with_counts, graph_data, knowledge_points_with_course, overview_payload
from .serializers import (
    chunk_payload,
    course_payload,
    document_payload,
    knowledge_point_payload,
)
from .services.ingest import ingest_document

ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown", ".pdf", ".docx"}
ALLOWED_SOURCE_TYPES = {"txt", "md", "markdown", "pdf", "docx"}


class OverviewView(APIView):
    def get(self, request):
        return Response(overview_payload())


class CourseListView(APIView):
    def get(self, request):
        courses = courses_with_counts()
        return Response([course_payload(course) for course in courses])


class KnowledgePointListView(APIView):
    def get(self, request):
        query = Q()
        course_uid = request.query_params.get("courseId")
        if course_uid:
            query &= Q(course__uid=course_uid)
        search = (request.query_params.get("search") or "").strip()
        if search:
            query &= Q(name__icontains=search) | Q(chapter__icontains=search) | Q(uid__icontains=search)
        queryset = knowledge_points_with_course().filter(query)
        try:
            limit = min(500, max(1, int(request.query_params.get("limit", 200))))
        except ValueError:
            limit = 200
        total = queryset.count()
        items = [knowledge_point_payload(point) for point in queryset[:limit]]
        return Response({"items": items, "total": total})


class KnowledgePointDetailView(APIView):
    def get(self, request, uid: str):
        point = KnowledgePoint.objects.select_related("course").filter(uid=uid).first()
        if not point:
            return Response(
                {"detail": "知识点不存在", "code": "KNOWLEDGE_POINT_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        chunks = (
            DocumentChunk.objects.filter(knowledge_point=point)
            .select_related("document", "course")
            .order_by("document_id", "ordinal")[:8]
        )
        payload = knowledge_point_payload(point)
        payload["chunkCount"] = point.chunks.count()
        payload["chunks"] = [
            {
                "id": chunk.uid,
                "title": chunk.title,
                "chapter": chunk.chapter,
                "source": chunk.source_name,
                "documentId": chunk.document.uid,
                "documentTitle": chunk.document.title,
                "content": chunk.content[:600],
                "ordinal": chunk.ordinal,
            }
            for chunk in chunks
        ]
        return Response(payload)


class GraphView(APIView):
    def get(self, request):
        return Response(graph_data())


class DocumentListCreateView(APIView):
    def get(self, request):
        query = Document.objects.select_related("course")
        course_uid = request.query_params.get("courseId")
        if course_uid:
            query = query.filter(course__uid=course_uid)
        status_value = request.query_params.get("status")
        if status_value:
            query = query.filter(status=status_value)
        search = (request.query_params.get("q") or "").strip()
        if search:
            query = query.filter(Q(title__icontains=search) | Q(source_name__icontains=search))
        total = query.count()
        items = [document_payload(doc) for doc in query[:200]]
        return Response({"items": items, "total": total})

    def post(self, request):
        course_uid = request.data.get("courseId")
        course = Course.objects.filter(uid=course_uid).first()
        if not course:
            return Response(
                {"detail": "请选择有效的课程", "code": "INVALID_COURSE"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        upload = request.FILES.get("file")
        if not upload:
            return Response(
                {"detail": "请选择要上传的文档", "code": "MISSING_FILE"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        extension = Path(upload.name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            return Response(
                {"detail": "仅支持 TXT、Markdown、PDF、DOCX 文档", "code": "UNSUPPORTED_FILE"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload.size > 25 * 1024 * 1024:
            return Response(
                {"detail": "文档大小不能超过 25 MB", "code": "FILE_TOO_LARGE"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        knowledge_point = None
        knowledge_point_uid = request.data.get("knowledgePointId")
        if knowledge_point_uid:
            knowledge_point = KnowledgePoint.objects.filter(
                uid=knowledge_point_uid, course=course
            ).first()
            if not knowledge_point:
                return Response(
                    {"detail": "知识点不属于当前课程", "code": "INVALID_KNOWLEDGE_POINT"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        title = (request.data.get("title") or Path(upload.name).stem).strip()[:255]
        document_uid = f"DOC-{course.short_name}-{uuid.uuid4().hex[:8].upper()}"
        source_type = extension.lstrip(".")
        source_name = (request.data.get("sourceName") or f"《{course.name}》· {title}")[:255]
        stored_name = f"uploads/{request.user.id}/{uuid.uuid4().hex}{extension}"
        saved_path = default_storage.save(stored_name, upload)
        absolute_path = Path(settings.MEDIA_ROOT) / saved_path

        document = Document.objects.create(
            uid=document_uid,
            course=course,
            knowledge_point=knowledge_point,
            title=title,
            source_name=source_name,
            source_type=source_type,
            storage_path=str(absolute_path),
            original_filename=upload.name[:255],
            mime=getattr(upload, "content_type", "")[:128],
            byte_size=upload.size,
            status="processing",
            uploaded_by=request.user,
        )
        try:
            ingest_document(document)
        except Exception as exc:
            # The document row remains visible with a failed status and a
            # human-readable reason instead of disappearing after upload.
            document.refresh_from_db()
            payload = document_payload(document)
            payload["detail"] = str(exc)
            return Response(payload, status=status.HTTP_201_CREATED)
        document.refresh_from_db()
        return Response(document_payload(document), status=status.HTTP_201_CREATED)


class DocumentDetailView(APIView):
    def delete(self, request, uid: str):
        document = Document.objects.filter(uid=uid).first()
        if not document:
            return Response(
                {"detail": "文档不存在", "code": "DOCUMENT_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if document.storage_path:
            try:
                custom_path = Path(document.storage_path).resolve()
                media_root = Path(settings.MEDIA_ROOT).resolve()
                if custom_path.is_relative_to(media_root) and custom_path.exists():
                    custom_path.unlink()
            except (OSError, ValueError):
                pass
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentReindexView(APIView):
    def post(self, request, uid: str):
        document = Document.objects.filter(uid=uid).first()
        if not document:
            return Response(
                {"detail": "文档不存在", "code": "DOCUMENT_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not document.storage_path:
            return Response(
                {"detail": "该文档没有可重新解析的源文件", "code": "NO_SOURCE_FILE"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            ingest_document(document)
        except Exception as exc:
            document.refresh_from_db()
            return Response(
                {"detail": str(exc), "code": "REINDEX_FAILED", "document": document_payload(document)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        document.refresh_from_db()
        return Response(document_payload(document))


class DocumentChunkListView(APIView):
    def get(self, request, uid: str):
        document = Document.objects.filter(uid=uid).prefetch_related("chunks").first()
        if not document:
            return Response(
                {"detail": "文档不存在", "code": "DOCUMENT_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )
        items = [
            chunk_payload(chunk) for chunk in document.chunks.select_related("course", "knowledge_point")
        ]
        return Response({"items": items, "total": len(items)})
