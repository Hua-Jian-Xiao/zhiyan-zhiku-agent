from __future__ import annotations

import time

from django.utils import timezone

from .models import Course, Document, DocumentChunk, KnowledgePoint


def to_epoch_ms(value) -> int:
    if not value:
        return int(time.time() * 1000)
    return int(value.timestamp() * 1000)


def date_string(value) -> str:
    if not value:
        return ""
    return timezone.localtime(value).strftime("%Y-%m-%d")


def course_payload(course: Course) -> dict:
    return {
        "id": course.uid,
        "code": course.code,
        "name": course.name,
        "shortName": course.short_name,
        "teacher": course.teacher,
        "school": course.school,
        "description": course.description,
        "category": course.category,
        "coverUrl": course.cover_url,
        "sourceUrl": course.source_url,
        "popularity": course.popularity,
        "knowledgePointCount": getattr(course, "kp_count", None)
        if getattr(course, "kp_count", None) is not None
        else course.knowledge_points.count(),
        "documentCount": getattr(course, "doc_count", None)
        if getattr(course, "doc_count", None) is not None
        else course.documents.count(),
        "color": course.color,
        "legacyCourseId": course.legacy_course_id,
        "isLegacyImport": course.uid.startswith("legacy-course-"),
        "updatedAt": date_string(course.updated_at),
    }


def knowledge_point_payload(point: KnowledgePoint) -> dict:
    return {
        "id": point.uid,
        "name": point.name,
        "course": point.course.name,
        "courseId": point.course.uid,
        "courseSourceUrl": point.course.source_url,
        "courseCoverUrl": point.course.cover_url,
        "chapter": point.chapter,
        "chapterNo": point.chapter_no,
        "difficulty": point.difficulty,
        "description": point.description,
        "tags": point.tags or [],
        "chunkCount": getattr(point, "chunk_count", None)
        if getattr(point, "chunk_count", None) is not None
        else point.chunks.count(),
        "updatedAt": date_string(point.updated_at),
    }


def graph_payload(categories, nodes, edges) -> dict:
    prerequisites: dict[str, list[str]] = {}
    for edge in edges:
        prerequisites.setdefault(edge.target.uid, []).append(edge.source.uid)

    return {
        "categories": [
            {"key": category.key, "label": category.label, "color": category.color}
            for category in categories
        ],
        "nodes": [
            {
                "id": node.uid,
                "name": node.name,
                "category": node.category_id,
                "description": node.description,
                "prerequisites": prerequisites.get(node.uid, []),
                "relatedCourse": node.related_course_label
                or (node.related_course.name if node.related_course else "课程大纲"),
                "difficulty": node.difficulty,
            }
            for node in nodes
        ],
        "edges": [
            {
                "source": edge.source.uid,
                "target": edge.target.uid,
                "reason": edge.reason,
            }
            for edge in edges
        ],
    }


def document_payload(document: Document) -> dict:
    return {
        "id": document.uid,
        "courseId": document.course.uid,
        "courseName": document.course.name,
        "title": document.title,
        "sourceName": document.source_name,
        "sourceType": document.source_type,
        "status": document.status,
        "chunkCount": document.chunk_count,
        "byteSize": document.byte_size,
        "createdAt": to_epoch_ms(document.created_at),
        "updatedAt": to_epoch_ms(document.updated_at),
        "errorMessage": document.error_message or None,
    }


def chunk_payload(chunk: DocumentChunk, score: float | None = None) -> dict:
    knowledge_point = chunk.knowledge_point
    return {
        "id": chunk.uid,
        "knowledgePointId": knowledge_point.uid if knowledge_point else "",
        "title": chunk.title,
        "course": chunk.course.name,
        "source": chunk.source_name,
        "chapter": chunk.chapter,
        "content": chunk.content,
        "tags": chunk.tags or [],
        "score": round(score if score is not None else 0.0, 3),
    }
