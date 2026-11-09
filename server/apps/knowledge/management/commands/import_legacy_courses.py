"""Import course metadata from the course dataset ``course_recommend`` database.

This command is additive: it never deletes existing courses. Curated courses
that already carry a ``legacy_course_id`` keep their hand-written metadata;
every other dataset row is created with a stable ``legacy-course-{id}`` uid.
Re-running the command refreshes previously imported rows instead of creating
duplicates.

Usage:
    python manage.py import_legacy_courses
    python manage.py import_legacy_courses --dry-run

Connection defaults come from the current Django DB settings. The dataset
database name defaults to ``course_recommend``; override it with ``LEGACY_DB_NAME``.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

import pymysql
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.knowledge.models import Course, LegacyImportMap

COLOR_PALETTE = (
    "#7d302f",
    "#3d5266",
    "#4f6b54",
    "#a37b2b",
    "#6b5563",
    "#8a4a3c",
    "#5f6b54",
    "#6d4f3b",
)
SAFE_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
URL_CODE_RE = re.compile(r"/course/([A-Za-z0-9_-]{1,32})")
ASCII_PREFIX_RE = re.compile(r"^[A-Za-z0-9+#.]+")
PUNCT_RE = re.compile(r"[\s()（）\[\]【】·:：/\\、，]+")
POPULARITY_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(万)?")


def _text(value: Any, limit: int | None = None) -> str:
    """Normalize whitespace and optionally clamp to a model field length."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit] if limit else text


def _popularity(value: Any) -> int:
    """Parse legacy strings such as ``599547 人`` or ``5.6 万``."""
    text = str(value or "").replace(",", "")
    match = POPULARITY_RE.search(text)
    if not match:
        return 0
    number = float(match.group(1))
    if match.group(2):
        number *= 10000
    return int(number)


def _code(row: dict[str, Any]) -> str:
    raw = _text(row.get("course_ID"), 200)
    if SAFE_CODE_RE.fullmatch(raw):
        return raw
    # A few legacy rows stored the full course URL in course_ID.
    match = URL_CODE_RE.search(raw)
    if match:
        return match.group(1)
    return f"LEG-{row['id']}"


def _short_name(name: str, legacy_id: int) -> str:
    text = PUNCT_RE.sub("", _text(name))
    if not text:
        return f"L{legacy_id}"
    ascii_match = ASCII_PREFIX_RE.match(text)
    if ascii_match:
        return ascii_match.group(0)[:6]
    return text[:3]


def _description(row: dict[str, Any]) -> str:
    summary = _text(row.get("summary"))
    if summary:
        return summary
    parts = [part for part in (row.get("school"), row.get("teacher"), row.get("type")) if part]
    return " · ".join(str(part) for part in parts) or "计算机学科课程。"


def _checksum(row: dict[str, Any]) -> str:
    raw = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Command(BaseCommand):
    help = "把课程数据集 course_recommend 的课程元数据导入智研知库课程表"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只统计将要新增/更新的数量，不写入数据库",
        )

    def _fetch_rows(self) -> list[dict[str, Any]]:
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
                "或通过 LEGACY_DB_NAME / LEGACY_DB_HOST / LEGACY_DB_USER / "
                "LEGACY_DB_PASSWORD 指定连接信息。"
                f" 原始错误：{exc}"
            ) from exc

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, course_ID, name, poster, teacher, school, student,
                           summary, type, course_url, video_url
                    FROM courses
                    ORDER BY id
                    """
                )
                return list(cursor.fetchall())
        except pymysql.MySQLError as exc:
            raise CommandError(f"读取数据集课程表失败：{exc}") from exc
        finally:
            connection.close()

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        raw_rows = self._fetch_rows()
        rows = [
            row
            for row in raw_rows
            if row.get("id") is not None and _text(row.get("name"))
        ]
        skipped = len(raw_rows) - len(rows)
        if not rows:
            raise CommandError("课程数据集中没有可导入的课程数据")

        # Keep the curated core courses first, then show popular legacy courses.
        rows.sort(key=lambda row: (-_popularity(row.get("student")), int(row["id"])))

        created = updated = curated = mapped = 0
        with transaction.atomic():
            for rank, row in enumerate(rows, start=1):
                legacy_id = int(row["id"])
                uid = f"legacy-course-{legacy_id}"
                name = _text(row.get("name"), 128)
                teacher = _text(row.get("teacher"), 64)
                school = _text(row.get("school"), 128)
                category = _text(row.get("type"), 64) or "计算机科学"
                description = _description(row)
                cover_url = _text(row.get("poster"), 500)
                source_url = _text(row.get("course_url"), 500)
                video_url = _text(row.get("video_url"), 500)
                popularity = _popularity(row.get("student"))
                color = COLOR_PALETTE[legacy_id % len(COLOR_PALETTE)]

                course = Course.objects.filter(legacy_course_id=legacy_id).first()
                if course is None:
                    course = Course.objects.filter(uid=uid).first()

                if course is None:
                    course = Course(
                        uid=uid,
                        code=_code(row),
                        name=name,
                        short_name=_short_name(name, legacy_id),
                        teacher=teacher,
                        school=school,
                        description=description,
                        cover_url=cover_url,
                        category=category,
                        color=color,
                        source_url=source_url,
                        video_url=video_url,
                        popularity=popularity,
                        legacy_course_id=legacy_id,
                        sort_order=1000 + rank,
                    )
                    if not dry_run:
                        course.save()
                    created += 1
                elif course.uid.startswith("legacy-course-"):
                    # Previously imported row: refresh its metadata in place.
                    if not dry_run:
                        course.code = _code(row)
                        course.name = name
                        course.short_name = _short_name(name, legacy_id)
                        course.teacher = teacher
                        course.school = school
                        course.description = description
                        course.cover_url = cover_url or course.cover_url
                        course.category = category
                        course.color = color
                        course.source_url = source_url or course.source_url
                        course.video_url = video_url or course.video_url
                        course.popularity = popularity
                        course.legacy_course_id = legacy_id
                        course.sort_order = 1000 + rank
                        course.save()
                    updated += 1
                else:
                    # Curated core course already mapped to this legacy row.
                    # Its copy and media are managed by seed/manifest.py, so
                    # never overwrite them with legacy values.
                    if not dry_run and not course.legacy_course_id:
                        course.legacy_course_id = legacy_id
                        course.save(update_fields=["legacy_course_id"])
                    curated += 1

                if not dry_run:
                    LegacyImportMap.objects.update_or_create(
                        entity_type="course",
                        legacy_table="courses",
                        legacy_id=legacy_id,
                        defaults={"new_uid": course.uid, "checksum": _checksum(row)},
                    )
                    mapped += 1

        prefix = "预览完成" if dry_run else "导入完成"
        message = (
            f"{prefix}：新增 {created} 门，刷新 {updated} 门，"
            f"沿用核心课程 {curated} 门，写入映射 {mapped} 条，"
            f"跳过空记录 {skipped} 条，当前课程总数 {Course.objects.count()} 门"
        )
        self.stdout.write(self.style.SUCCESS(message))
