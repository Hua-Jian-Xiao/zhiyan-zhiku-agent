import json
import re
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.agent.models import Conversation
from apps.knowledge.models import Course, Document, DocumentChunk, KnowledgePoint
from apps.retrieval.models import RetrievalLog
from seed.builder import run_seed
from django.test import TestCase


def parse_sse(raw: str) -> list[tuple[str, dict]]:
    events = []
    for block in raw.split("\n\n"):
        if not block.strip() or block.startswith(":"):
            continue
        event = "message"
        data_lines = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
        if data_lines:
            events.append((event, json.loads("\n".join(data_lines))))
    return events


@override_settings(DEEPSEEK_API_KEY="", LLM_PROVIDER="local")
class RagApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        run_seed(reset=True)

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(username="student")
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_auth_and_public_stats(self):
        client = APIClient()
        response = client.post(
            "/api/v1/auth/login/",
            {"username": "student", "password": "student123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["displayName"], "林晓")

        denied = client.post(
            "/api/v1/auth/login/",
            {"username": "student", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(denied.status_code, 401)

        stats = client.get("/api/v1/public/stats/")
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.data["courseCount"], 8)
        self.assertGreater(stats.data["knowledgePointCount"], 0)
        self.assertGreater(stats.data["chunkCount"], 0)
        self.assertEqual(stats.data["graphNodeCount"], 23)

        me = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["user"]["username"], "student")

    def test_register_new_account_and_duplicate_guard(self):
        client = APIClient()
        response = client.post(
            "/api/v1/auth/register/",
            {
                "username": "new_reader",
                "password": "reader123",
                "displayName": "新读者",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(response.data["token"])
        self.assertEqual(response.data["user"]["displayName"], "新读者")
        self.assertTrue(User.objects.filter(username="new_reader").exists())

        duplicate = client.post(
            "/api/v1/auth/register/",
            {"username": "new_reader", "password": "reader123"},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 409)

        login = client.post(
            "/api/v1/auth/login/",
            {"username": "new_reader", "password": "reader123"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)

    def test_overview_graph_and_config(self):
        overview = self.client.get("/api/v1/knowledge-base/overview/")
        self.assertEqual(overview.status_code, 200)
        self.assertEqual(overview.data["courseCount"], 8)
        self.assertEqual(len(overview.data["courses"]), 8)
        self.assertIn("knowledgePoints", overview.data)

        graph = self.client.get("/api/v1/graph/")
        self.assertEqual(graph.status_code, 200)
        self.assertEqual(len(graph.data["categories"]), 4)
        self.assertEqual(len(graph.data["nodes"]), 23)
        self.assertEqual(len(graph.data["edges"]), 33)
        node_ids = {node["id"] for node in graph.data["nodes"]}
        self.assertTrue(all(edge["source"] in node_ids for edge in graph.data["edges"]))
        self.assertTrue(all(edge["target"] in node_ids for edge in graph.data["edges"]))

        config = self.client.get("/api/v1/rag/config/")
        self.assertEqual(config.status_code, 200)
        self.assertEqual(config.data["topK"], 5)
        updated = self.client.put(
            "/api/v1/rag/config/",
            {"topK": 7, "threshold": 0.55, "retrievalMode": "vector"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["topK"], 7)
        self.assertEqual(updated.data["retrievalMode"], "vector")

    def test_retrieval_all_modes_and_logging(self):
        for mode in ("hybrid", "vector", "keyword"):
            response = self.client.post(
                "/api/v1/retrieval/query/",
                {
                    "query": "RAG 的完整检索链路是什么？",
                    "topK": 5,
                    "threshold": 0.3,
                    "retrievalMode": mode,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200, response.content)
            self.assertIn("chunks", response.data)
            self.assertIn("metrics", response.data)
            self.assertEqual(response.data["config"]["retrievalMode"], mode)
            self.assertGreaterEqual(len(response.data["chunks"]), 1)
            fields = response.data["chunks"][0]
            for key in ("id", "knowledgePointId", "title", "course", "source", "chapter", "content", "tags", "score"):
                self.assertIn(key, fields)
        self.assertGreater(RetrievalLog.objects.count(), 0)

    def test_agent_stream_fallback_and_persistence(self):
        assistant_id = "msg_test_assistant"
        user_id = "msg_test_user"
        response = self.client.post(
            f"/api/v1/conversations/conv_test_stream/stream/",
            {
                "query": "RAG 的完整检索链路是什么？",
                "topK": 5,
                "threshold": 0.72,
                "retrievalMode": "hybrid",
                "conversationTitle": "RAG 测试会话",
                "userMessageId": user_id,
                "assistantMessageId": assistant_id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        raw = b"".join(response.streaming_content).decode("utf-8")
        events = parse_sse(raw)
        event_names = [name for name, _ in events]
        self.assertIn("step", event_names)
        self.assertIn("tool", event_names)
        self.assertIn("retrieval", event_names)
        self.assertIn("citations", event_names)
        self.assertIn("delta", event_names)
        self.assertEqual(event_names[-1], "done")

        conversation = Conversation.objects.get(id="conv_test_stream", user=self.user)
        self.assertEqual(conversation.title, "RAG 测试会话")
        self.assertEqual(conversation.messages.count(), 2)
        assistant = conversation.messages.get(id=assistant_id)
        self.assertEqual(assistant.status, "done")
        self.assertGreater(len(assistant.content), 0)
        self.assertTrue(assistant.agent_run.citations.exists())
        self.assertTrue(assistant.agent_run.tools.exists())
        self.assertGreater(assistant.agent_run.steps.count(), 0)

        reloaded = self.client.get("/api/v1/conversations/conv_test_stream/")
        self.assertEqual(reloaded.status_code, 200)
        messages = reloaded.data["messages"]
        self.assertEqual(len(messages), 2)
        assistant_payload = next(item for item in messages if item["id"] == assistant_id)
        self.assertTrue(assistant_payload["citations"])
        self.assertEqual(len(assistant_payload["trace"]["steps"]), 4)
        self.assertTrue(assistant_payload["trace"]["chunks"])

    def test_document_upload_retrieval_and_cascade(self):
        course = Course.objects.get(uid="course-ml")
        point = KnowledgePoint.objects.filter(course=course).first()
        content = (
            "# 测试文档\n\n## 第 9 章 量子检索\n\n"
            "### 9.1 量子检索测试知识点\n\n"
            "量子检索测试是一种用于验证文档入库、分块和检索链路的独特术语。"
            "当用户查询量子检索测试时，系统应当召回本段文字并展示来源与知识点。"
        )
        upload = SimpleUploadedFile(
            "quantum-test.md", content.encode("utf-8"), content_type="text/markdown"
        )
        response = self.client.post(
            "/api/v1/documents/",
            {
                "courseId": course.uid,
                "knowledgePointId": point.uid,
                "title": "量子检索测试文档",
                "file": upload,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.content)
        document_id = response.data["id"]
        document = Document.objects.get(uid=document_id)
        self.assertEqual(document.status, "ready")
        self.assertGreater(document.chunk_count, 0)
        self.assertTrue(DocumentChunk.objects.filter(document=document).exists())

        search = self.client.post(
            "/api/v1/retrieval/query/",
            {
                "query": "量子检索测试",
                "topK": 5,
                "threshold": 0.3,
                "retrievalMode": "keyword",
            },
            format="json",
        )
        self.assertEqual(search.status_code, 200)
        self.assertTrue(
            any("量子检索测试" in chunk["content"] for chunk in search.data["chunks"])
        )

        delete = self.client.delete(f"/api/v1/documents/{document_id}/")
        self.assertEqual(delete.status_code, 204)
        self.assertFalse(Document.objects.filter(uid=document_id).exists())
        self.assertFalse(DocumentChunk.objects.filter(document_id=document.id).exists())

    def test_conversation_crud(self):
        created = self.client.post(
            "/api/v1/conversations/",
            {"id": "conv_test_crud", "title": "临时会话"},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        listing = self.client.get("/api/v1/conversations/")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(
            any(item["id"] == "conv_test_crud" for item in listing.data["conversations"])
        )
        cleared = self.client.delete("/api/v1/conversations/conv_test_crud/messages/")
        self.assertEqual(cleared.status_code, 204)
        deleted = self.client.delete("/api/v1/conversations/conv_test_crud/")
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(Conversation.objects.filter(id="conv_test_crud").exists())

    def test_profile_update_and_avatar_upload(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            avatar = SimpleUploadedFile(
                "avatar.png",
                b"\x89PNG\r\n\x1a\n" + b"0" * 64,
                content_type="image/png",
            )
            response = self.client.patch(
                "/api/v1/auth/profile/",
                {
                    "displayName": "林晓新",
                    "email": "linxiao@example.com",
                    "major": "人工智能",
                    "grade": "本科四年级",
                    "bio": "研究 RAG 与知识图谱。",
                    "avatar": avatar,
                },
                format="multipart",
            )
            self.assertEqual(response.status_code, 200, response.content)
            user = response.data["user"]
            self.assertEqual(user["displayName"], "林晓新")
            self.assertEqual(user["email"], "linxiao@example.com")
            self.assertIn("/media/avatars/", user["avatarUrl"])
            self.user.refresh_from_db()
            self.assertEqual(self.user.display_name, "林晓新")
            self.assertTrue(self.user.avatar.name)

    def test_change_password(self):
        wrong = self.client.post(
            "/api/v1/auth/change-password/",
            {"oldPassword": "wrong-password", "newPassword": "student456"},
            format="json",
        )
        self.assertEqual(wrong.status_code, 400)

        response = self.client.post(
            "/api/v1/auth/change-password/",
            {"oldPassword": "student123", "newPassword": "student456"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        login = APIClient().post(
            "/api/v1/auth/login/",
            {"username": "student", "password": "student456"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)

    def test_password_reset_with_security_question(self):
        client = APIClient()
        question = client.get("/api/v1/auth/security-question/?username=student")
        self.assertEqual(question.status_code, 200, question.content)
        self.assertEqual(question.data["securityQuestion"], "我最喜欢的课程是？")

        wrong = client.post(
            "/api/v1/auth/reset-password/",
            {
                "username": "student",
                "answer": "错误答案",
                "newPassword": "student789",
            },
            format="json",
        )
        self.assertEqual(wrong.status_code, 400)

        reset = client.post(
            "/api/v1/auth/reset-password/",
            {
                "username": "student",
                "answer": "机器学习",
                "newPassword": "student789",
            },
            format="json",
        )
        self.assertEqual(reset.status_code, 200, reset.content)
        login = client.post(
            "/api/v1/auth/login/",
            {"username": "student", "password": "student789"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
