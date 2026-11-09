from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings
from django.db import transaction

from apps.accounts.models import User
from apps.knowledge.models import (
    Course,
    Document,
    DocumentChunk,
    GraphCategory,
    GraphEdge,
    GraphNode,
    KnowledgePoint,
    LegacyImportMap,
)
from apps.knowledge.services.ingest import ingest_document
from apps.retrieval.models import RagSettings
from seed.manifest import (
    COURSES,
    GRAPH_CATEGORIES,
    GRAPH_NODES,
    LEGACY_KP_MAP,
    TAG_KEYWORDS,
)

SEED_DIR = Path(__file__).resolve().parent
CONTENT_DIR = SEED_DIR / "content"
CHAPTER_RE = re.compile(r"^##\s+(.+)$")
SECTION_RE = re.compile(r"^###\s+(.+)$")
NUMBERING_RE = re.compile(r"^[\d.\s、]+")


def clean_title(value: str) -> str:
    return NUMBERING_RE.sub("", value).strip()


def parse_markdown(path: Path) -> list[dict]:
    chapter = ""
    chapter_no = 0
    section = ""
    content: list[str] = []
    sections: list[dict] = []

    def flush():
        nonlocal content
        if section and content:
            body = "\n".join(content).strip()
            if body:
                sections.append(
                    {
                        "chapter": chapter,
                        "chapter_no": chapter_no,
                        "title": clean_title(section),
                        "raw_title": section,
                        "content": body,
                    }
                )
        content = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        chapter_match = CHAPTER_RE.match(line)
        section_match = SECTION_RE.match(line)
        if chapter_match and not section_match:
            flush()
            chapter_no += 1
            chapter = chapter_match.group(1).strip()
            section = ""
            continue
        if section_match:
            flush()
            section = section_match.group(1).strip()
            continue
        if line.startswith("# "):
            continue
        if section:
            content.append(line)
    flush()
    return sections


def _description(text: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    return " ".join(paragraphs[:2])[:320]


def _tags(course: dict, text: str, title: str) -> list[str]:
    tags = [course["short_name"], course["name"]]
    for keyword in TAG_KEYWORDS:
        if keyword in text and keyword not in tags:
            tags.append(keyword)
        if len(tags) >= 6:
            break
    if title not in tags:
        tags.append(title)
    return tags[:8]


def purge_business_data() -> None:
    from apps.agent.models import AgentRun, Conversation
    from apps.retrieval.models import RetrievalLog

    Conversation.objects.all().delete()
    RetrievalLog.objects.all().delete()
    RagSettings.objects.all().delete()
    DocumentChunk.objects.all().delete()
    Document.objects.all().delete()
    GraphEdge.objects.all().delete()
    GraphNode.objects.all().delete()
    GraphCategory.objects.all().delete()
    KnowledgePoint.objects.all().delete()
    Course.objects.all().delete()
    LegacyImportMap.objects.all().delete()


def seed_users() -> tuple[User, User]:
    student, _ = User.objects.get_or_create(
        username="student",
        defaults={
            "display_name": "林晓",
            "role": "计算机科学 · 学习者",
            "avatar_text": "林",
            "major": "计算机科学与技术",
            "grade": "本科",
        },
    )
    student.display_name = "林晓"
    student.role = "计算机科学 · 学习者"
    student.avatar_text = "林"
    student.security_question = "我最喜欢的课程是？"
    student.set_security_answer("机器学习")
    student.set_password("student123")
    student.save()

    admin, _ = User.objects.get_or_create(
        username="admin",
        defaults={"display_name": "管理员", "role": "知识库管理员", "is_staff": True, "is_superuser": True},
    )
    admin.display_name = "管理员"
    admin.role = "知识库管理员"
    admin.avatar_text = "管"
    admin.is_staff = True
    admin.is_superuser = True
    admin.security_question = "我的管理口令是？"
    admin.set_security_answer("zhiyan")
    admin.set_password("zhiyan123")
    admin.save()
    return student, admin


def seed_courses(student: User) -> dict[str, Course]:
    course_map: dict[str, Course] = {}
    for order, item in enumerate(COURSES, start=1):
        course, _ = Course.objects.update_or_create(
            uid=item["uid"],
            defaults={
                "code": item["code"],
                "name": item["name"],
                "short_name": item["short_name"],
                "teacher": item["teacher"],
                "school": item["school"],
                "description": item["description"],
                "category": item["category"],
                "color": item["color"],
                "cover_url": item.get("cover_url", ""),
                "source_url": item.get("source_url", ""),
                "popularity": item["popularity"],
                "legacy_course_id": item["legacy_course_id"],
                "sort_order": order,
            },
        )
        course_map[item["uid"]] = course
        if item["legacy_course_id"]:
            LegacyImportMap.objects.update_or_create(
                entity_type="course",
                legacy_table="courses",
                legacy_id=item["legacy_course_id"],
                defaults={"new_uid": course.uid},
            )
    return course_map


def seed_knowledge_and_documents(
    course_map: dict[str, Course], student: User
) -> tuple[list[KnowledgePoint], list[Document]]:
    all_points: list[KnowledgePoint] = []
    documents: list[Document] = []
    for item in COURSES:
        course = course_map[item["uid"]]
        markdown_path = CONTENT_DIR / item["content"]
        if not markdown_path.exists():
            raise FileNotFoundError(f"Missing seed content: {markdown_path}")
        sections = parse_markdown(markdown_path)
        if len(sections) < 6:
            raise ValueError(
                f"{item['name']} 的知识点数量为 {len(sections)}，至少应为 6"
            )

        for index, section in enumerate(sections, start=1):
            uid = f"KP-{item['short_name']}-{index:03d}"
            point, _ = KnowledgePoint.objects.update_or_create(
                uid=uid,
                defaults={
                    "course": course,
                    "name": section["title"],
                    "chapter": section["chapter"],
                    "chapter_no": section["chapter_no"],
                    "difficulty": "入门" if section["chapter_no"] == 1 else "进阶",
                    "description": _description(section["content"]),
                    "tags": _tags(item, section["content"], section["title"]),
                    "legacy_node_id": LEGACY_KP_MAP.get(section["title"]),
                    "sort_order": index,
                },
            )
            all_points.append(point)
            if point.legacy_node_id:
                LegacyImportMap.objects.update_or_create(
                    entity_type="knowledge_point",
                    legacy_table="knowledge_nodes",
                    legacy_id=point.legacy_node_id,
                    defaults={"new_uid": point.uid},
                )

        doc_uid = f"DOC-{item['short_name']}-001"
        document, _ = Document.objects.update_or_create(
            uid=doc_uid,
            defaults={
                "course": course,
                "title": f"{item['name']} · 课程讲义",
                "source_name": f"《{item['name']}》课程讲义",
                "source_type": "md",
                "storage_path": str(markdown_path),
                "original_filename": markdown_path.name,
                "mime": "text/markdown",
                "byte_size": markdown_path.stat().st_size,
                "status": "processing",
                "uploaded_by": student,
                "legacy_course_id": item["legacy_course_id"],
            },
        )
        document = ingest_document(document)
        documents.append(document)
    return all_points, documents


def seed_graph(course_map: dict[str, Course]) -> tuple[int, int]:
    category_map: dict[str, GraphCategory] = {}
    for item in GRAPH_CATEGORIES:
        category, _ = GraphCategory.objects.update_or_create(
            key=item["key"],
            defaults={
                "label": item["label"],
                "color": item["color"],
                "sort_order": item["sort_order"],
            },
        )
        category_map[item["key"]] = category

    point_map = {point.uid: point for point in KnowledgePoint.objects.all()}
    node_map: dict[str, GraphNode] = {}
    for order, item in enumerate(GRAPH_NODES, start=1):
        related_course = course_map.get(item.get("related_course_uid"))
        node, _ = GraphNode.objects.update_or_create(
            uid=item["uid"],
            defaults={
                "name": item["name"],
                "category": category_map[item["category"]],
                "description": item["description"],
                "difficulty": item["difficulty"],
                "related_course": related_course,
                "related_course_label": item.get("related_course_label", ""),
                "knowledge_point": point_map.get(item.get("knowledge_point_uid")),
                "legacy_node_id": item.get("legacy_node_id"),
                "sort_order": order,
            },
        )
        node_map[item["uid"]] = node
        if item.get("legacy_node_id"):
            LegacyImportMap.objects.update_or_create(
                entity_type="graph_node",
                legacy_table="knowledge_nodes",
                legacy_id=item["legacy_node_id"],
                defaults={"new_uid": node.uid},
            )

    edge_count = 0
    for item in GRAPH_NODES:
        target = node_map[item["uid"]]
        for prerequisite in item["prerequisites"]:
            source = node_map[prerequisite]
            GraphEdge.objects.update_or_create(
                source=source,
                target=target,
                relation="prerequisite",
                defaults={
                    "reason": f"学习「{target.name}」前需要掌握「{source.name}」",
                    "weight": 1.0,
                },
            )
            edge_count += 1
    return len(node_map), edge_count


def seed_rag_settings(users: list[User]) -> None:
    for user in users:
        RagSettings.objects.update_or_create(
            user=user,
            defaults={"top_k": 5, "threshold": 0.72, "retrieval_mode": "hybrid"},
        )


def run_seed(*, reset: bool = False) -> dict:
    if reset:
        purge_business_data()
    with transaction.atomic():
        student, admin = seed_users()
        course_map = seed_courses(student)
        points, documents = seed_knowledge_and_documents(course_map, student)
        node_count, edge_count = seed_graph(course_map)
        seed_rag_settings([student, admin])
    return {
        "courses": Course.objects.count(),
        "knowledgePoints": KnowledgePoint.objects.count(),
        "documents": Document.objects.count(),
        "chunks": DocumentChunk.objects.count(),
        "graphNodes": node_count,
        "graphEdges": edge_count,
    }
