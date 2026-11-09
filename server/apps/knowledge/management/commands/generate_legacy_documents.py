"""Generate one indexed Markdown document for every imported dataset course.

The course dataset database only stored course metadata and a small knowledge
graph, not full course handouts. This command turns each imported course and
its knowledge points into a Markdown "课程知识纲要", stores the source file
under ``server/media/generated/legacy_docs`` and runs the normal ingestion
pipeline so the document appears in the document library and becomes usable
for RAG retrieval.

Usage:
    python manage.py generate_legacy_documents
    python manage.py generate_legacy_documents --limit 3
    python manage.py generate_legacy_documents --dry-run
"""
from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.knowledge.models import Course, Document, KnowledgePoint
from apps.knowledge.services.ingest import ingest_document


class Command(BaseCommand):
    help = "为每门数据集课程生成课程知识纲要文档并建立向量索引"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只统计将新增/更新的文档数量，不写文件、不入库",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="只处理前 N 门课程，0 表示全部",
        )

    def _build_markdown(self, course: Course, points: list[KnowledgePoint]) -> str:
        category = course.category or "计算机学科"
        teacher = course.teacher or "课程团队"
        school = course.school or "在线课程"
        description = course.description.strip() or (
            f"《{course.name}》是{category}课程，由{teacher}讲授，"
            f"开设于{school}。本纲要用于梳理课程定位、核心知识点与学习路径。"
        )

        lines = [f"# {course.name}", "", "## 课程概览", "", description, ""]
        lines.append(f"- 课程编号：{course.code}")
        lines.append(f"- 主讲教师：{teacher}")
        lines.append(f"- 开设学校：{school}")
        lines.append(f"- 课程分类：{category}")
        if course.source_url:
            lines.append(f"- 课程链接：{course.source_url}")
        lines.append("")

        for point in points:
            chapter = point.chapter or "课程知识点"
            point_description = point.description.strip() or (
                f"「{point.name}」是《{course.name}》中的核心知识主题，"
                "建议结合课程案例理解其概念、方法与适用场景。"
            )
            lines.append(f"## {chapter}")
            lines.append("")
            lines.append(f"### {point.name}")
            lines.append("")
            lines.append(point_description)
            lines.append("")
            lines.append(
                f"学习建议：先理解「{point.name}」的基本定义，再结合《{course.name}》"
                "中的示例完成一次练习，并记录仍然不清楚的问题。"
            )
            lines.append("")

        lines.append("## 学习路径")
        lines.append("")
        lines.append(f"建议先完成《{course.name}》的课程概览，再按知识点顺序学习：")
        lines.append("")
        for index, point in enumerate(points, start=1):
            lines.append(f"{index}. {point.name}")
        lines.append("")
        lines.append("## 复习与自测")
        lines.append("")
        lines.append(
            "每完成一个知识点，尝试用自己的话解释核心概念，并回到课程资料核对。"
            "对于不熟悉的概念，可在 Agent 工作台提问并查看引用来源。"
        )
        lines.append("")
        return "\n".join(lines)

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        limit = int(options["limit"] or 0)

        courses = list(
            Course.objects.filter(uid__startswith="legacy-course-").order_by(
                "legacy_course_id", "id"
            )
        )
        if not courses:
            raise CommandError(
                "还没有导入数据集课程。请先运行 python manage.py import_legacy_courses"
            )
        if limit > 0:
            courses = courses[:limit]

        output_dir = Path(settings.MEDIA_ROOT) / "generated" / "legacy_docs"
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)

        student = get_user_model().objects.filter(username="student").first()
        created = updated = ingested = 0
        total_chunks = 0

        for course in courses:
            points = list(
                course.knowledge_points.all().order_by(
                    "chapter_no", "sort_order", "id"
                )
            )
            content = self._build_markdown(course, points)
            uid = f"DOC-LEG-{course.legacy_course_id}"
            path = output_dir / f"{uid}.md"
            existing = Document.objects.filter(uid=uid).first()

            if dry_run:
                created += int(existing is None)
                updated += int(existing is not None)
                continue

            path.write_text(content, encoding="utf-8")
            document, is_created = Document.objects.update_or_create(
                uid=uid,
                defaults={
                    "course": course,
                    "knowledge_point": None,
                    "title": f"{course.name} · 课程知识纲要",
                    "source_name": f"《{course.name}》课程知识纲要",
                    "source_type": "md",
                    "storage_path": str(path),
                    "original_filename": path.name,
                    "mime": "text/markdown",
                    "byte_size": path.stat().st_size,
                    "status": "processing",
                    "uploaded_by": student,
                    "legacy_course_id": course.legacy_course_id,
                },
            )
            document = ingest_document(document)
            document.refresh_from_db()
            total_chunks += document.chunk_count
            created += int(is_created)
            updated += int(not is_created)
            ingested += 1

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"预览完成：将新增 {created} 份，更新 {updated} 份，"
                    f"本次处理 {len(courses)} 门课程"
                )
            )
            return

        document_count = Document.objects.count()
        covered_courses = Document.objects.values("course_id").distinct().count()
        course_count = Course.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"生成完成：新增 {created} 份，更新 {updated} 份，"
                f"本次入库 {ingested} 份，生成 {total_chunks} 个向量片段；"
                f"文档总数 {document_count} 份，覆盖课程 {covered_courses}/{course_count} 门"
            )
        )
