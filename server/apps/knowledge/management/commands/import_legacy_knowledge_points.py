"""Create knowledge points for dataset courses from the course-kg links.

The course dataset ``course_recommend`` database stores a small knowledge graph in
``knowledge_nodes`` and ``course_knowledge``. Imported dataset courses start
with zero knowledge points, so this command attaches the linked nodes to the
matching dataset course. Courses without any link receive one fallback
"课程导论" point, which guarantees that every imported course appears in the
knowledge-point list.

Usage:
    python manage.py import_legacy_knowledge_points
    python manage.py import_legacy_knowledge_points --dry-run
"""
from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

import pymysql
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.knowledge.models import Course, KnowledgePoint

NODE_TYPE_LABELS = {
    "subject": "学科基础",
    "domain": "知识领域",
    "knowledge": "核心知识",
    "skill": "实践技能",
    "tool": "工具与框架",
}
DIFFICULTY_MAP = {
    1: "入门",
    2: "入门",
    3: "进阶",
    4: "高阶",
    5: "高阶",
}


def _difficulty(value: Any) -> str:
    try:
        return DIFFICULTY_MAP.get(int(value), "入门")
    except (TypeError, ValueError):
        return "入门"


class Command(BaseCommand):
    help = "基于课程数据集 knowledge_nodes / course_knowledge 为导入课程补齐知识点"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只统计将新增/更新的数量，不写入数据库",
        )

    def _fetch_legacy_rows(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        try:
            connection = pymysql.connect(
                host=os.getenv("LEGACY_DB_HOST") or os.getenv("DB_HOST", "127.0.0.1"),
                port=int(os.getenv("LEGACY_DB_PORT") or os.getenv("DB_PORT", "3306")),
                user=os.getenv("LEGACY_DB_USER") or os.getenv("DB_USER", "root"),
                password=os.getenv("LEGACY_DB_PASSWORD")
                if os.getenv("LEGACY_DB_PASSWORD") is not None
                else os.getenv("DB_PASSWORD", ""),
                database=os.getenv("LEGACY_DB_NAME", "course_recommend"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
        except pymysql.MySQLError as exc:
            raise CommandError(
                "无法连接课程数据集数据库 course_recommend。请确认数据集数据库存在，"
                f"或通过 LEGACY_DB_* 环境变量指定连接信息。原始错误：{exc}"
            ) from exc

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, node_type, description, difficulty, parent_id "
                    "FROM knowledge_nodes ORDER BY id"
                )
                nodes = list(cursor.fetchall())
                cursor.execute(
                    "SELECT id, course_id, knowledge_id, relation_type, weight "
                    "FROM course_knowledge ORDER BY id"
                )
                links = list(cursor.fetchall())
                return nodes, links
        except pymysql.MySQLError as exc:
            raise CommandError(f"读取旧知识点表失败：{exc}") from exc
        finally:
            connection.close()

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        nodes, links = self._fetch_legacy_rows()
        if not nodes:
            raise CommandError("课程数据集 knowledge_nodes 没有数据")

        node_map = {int(node["id"]): node for node in nodes}
        links_by_course: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for link in links:
            knowledge_id = int(link["knowledge_id"])
            if knowledge_id in node_map:
                links_by_course[int(link["course_id"])].append(link)

        imported_courses = list(
            Course.objects.filter(uid__startswith="legacy-course-").order_by(
                "legacy_course_id", "id"
            )
        )
        if not imported_courses:
            raise CommandError(
                "还没有导入数据集课程。请先运行 python manage.py import_legacy_courses"
            )

        created = updated = fallback = 0
        with transaction.atomic():
            for course in imported_courses:
                legacy_id = course.legacy_course_id
                if legacy_id is None:
                    continue
                course_links = links_by_course.get(int(legacy_id), [])
                if course_links:
                    for index, link in enumerate(course_links, start=1):
                        node = node_map[int(link["knowledge_id"])]
                        type_label = NODE_TYPE_LABELS.get(
                            str(node.get("node_type") or ""), "课程知识点"
                        )
                        uid = f"KP-LEG-{legacy_id}-{node['id']}"
                        defaults = {
                            "course": course,
                            "name": str(node["name"])[:160],
                            "chapter": type_label,
                            "chapter_no": 1,
                            "difficulty": _difficulty(node.get("difficulty")),
                            "description": (
                                str(node.get("description") or "").strip()
                                or f"《{course.name}》中的「{node['name']}」{type_label}，"
                                "是理解该课程知识体系的核心主题之一。"
                            ),
                            "tags": [
                                tag
                                for tag in (
                                    course.short_name,
                                    course.name,
                                    type_label,
                                    str(node["name"]),
                                )
                                if tag
                            ],
                            "legacy_node_id": int(node["id"]),
                            "sort_order": index,
                        }
                        exists = KnowledgePoint.objects.filter(uid=uid).exists()
                        if not dry_run:
                            KnowledgePoint.objects.update_or_create(
                                uid=uid, defaults=defaults
                            )
                        created += int(not exists)
                        updated += int(exists)
                else:
                    uid = f"KP-LEG-{legacy_id}-000"
                    defaults = {
                        "course": course,
                        "name": f"{course.name}导论"[:160],
                        "chapter": "课程导论",
                        "chapter_no": 1,
                        "difficulty": "入门",
                        "description": (
                            f"《{course.name}》课程导论，梳理课程定位、核心概念、"
                            "学习路径与先修关系。"
                        ),
                        "tags": [tag for tag in (course.short_name, course.name, "课程导论") if tag],
                        "legacy_node_id": None,
                        "sort_order": 1,
                    }
                    exists = KnowledgePoint.objects.filter(uid=uid).exists()
                    if not dry_run:
                        KnowledgePoint.objects.update_or_create(uid=uid, defaults=defaults)
                    created += int(not exists)
                    updated += int(exists)
                    fallback += 1

        total_points = KnowledgePoint.objects.count()
        covered_courses = KnowledgePoint.objects.values("course_id").distinct().count()
        total_courses = Course.objects.count()
        prefix = "预览完成" if dry_run else "补齐完成"
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}：新增 {created} 个，更新 {updated} 个，"
                f"其中兜底导论 {fallback} 个；"
                f"知识点总数 {total_points} 个，覆盖课程 {covered_courses}/{total_courses} 门"
            )
        )
