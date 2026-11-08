from __future__ import annotations

import re
import uuid

from django.db import transaction
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.retrieval.services.search import (
    get_user_config,
    normalize_config,
    save_user_config,
)

from .models import AgentRun, Conversation, Message
from .serializers import conversation_payload
from .services.orchestrator import run_agent_stream

VALID_ID = re.compile(r"^[A-Za-z0-9_-]{3,64}$")
DEFAULT_TITLE = "新的学习会话"


class EventStreamNegotiation(DefaultContentNegotiation):
    """APIView returns a raw StreamingHttpResponse, so skip renderer matching."""

    def select_renderer(self, request, renderers, format_suffix=None):
        renderer = renderers[0]
        return renderer, renderer.media_type


def _valid_id(value: str) -> bool:
    return bool(VALID_ID.fullmatch(value or ""))


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _title_from_query(query: str) -> str:
    compact = re.sub(r"\s+", " ", query).strip()
    return compact[:22] + ("…" if len(compact) > 22 else "")


class ConversationListCreateView(APIView):
    def get(self, request):
        conversations = (
            Conversation.objects.filter(user=request.user)
            .prefetch_related("messages")
            .order_by("-updated_at", "-created_at")
        )
        return Response({"conversations": [conversation_payload(item) for item in conversations]})

    def post(self, request):
        conversation_id = request.data.get("id") or _new_id("conv")
        if not _valid_id(conversation_id):
            return Response(
                {"detail": "会话 ID 格式不正确", "code": "INVALID_CONVERSATION_ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        existing = Conversation.objects.filter(id=conversation_id).first()
        if existing and existing.user_id != request.user.id:
            return Response(
                {"detail": "会话 ID 已被其他用户占用", "code": "CONVERSATION_CONFLICT"},
                status=status.HTTP_409_CONFLICT,
            )
        if existing:
            return Response(conversation_payload(existing))
        title = (request.data.get("title") or DEFAULT_TITLE).strip()[:120] or DEFAULT_TITLE
        conversation = Conversation.objects.create(
            id=conversation_id, user=request.user, title=title
        )
        return Response(conversation_payload(conversation), status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    def _get(self, request, conversation_id: str):
        return Conversation.objects.filter(id=conversation_id, user=request.user).prefetch_related("messages").first()

    def get(self, request, conversation_id: str):
        conversation = self._get(request, conversation_id)
        if not conversation:
            return Response(
                {"detail": "会话不存在", "code": "CONVERSATION_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(conversation_payload(conversation))

    def patch(self, request, conversation_id: str):
        conversation = self._get(request, conversation_id)
        if not conversation:
            return Response(
                {"detail": "会话不存在", "code": "CONVERSATION_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )
        title = str(request.data.get("title", "")).strip()[:120]
        if not title:
            return Response(
                {"detail": "会话标题不能为空", "code": "INVALID_TITLE"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        conversation.title = title
        conversation.save(update_fields=["title", "updated_at"])
        return Response(conversation_payload(conversation))

    def delete(self, request, conversation_id: str):
        conversation = self._get(request, conversation_id)
        if not conversation:
            return Response(status=status.HTTP_204_NO_CONTENT)
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConversationClearView(APIView):
    def delete(self, request, conversation_id: str):
        conversation = Conversation.objects.filter(
            id=conversation_id, user=request.user
        ).first()
        if not conversation:
            return Response(
                {"detail": "会话不存在", "code": "CONVERSATION_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )
        conversation.messages.all().delete()
        conversation.title = DEFAULT_TITLE
        conversation.save(update_fields=["title", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class MessageDeleteView(APIView):
    def delete(self, request, message_id: str):
        message = Message.objects.select_related("conversation").filter(
            id=message_id, conversation__user=request.user
        ).first()
        if not message:
            return Response(status=status.HTTP_204_NO_CONTENT)
        conversation = message.conversation
        message.delete()
        conversation.save(update_fields=["updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgentStreamView(APIView):
    content_negotiation_class = EventStreamNegotiation

    def post(self, request, conversation_id: str):
        if not _valid_id(conversation_id):
            return Response(
                {"detail": "会话 ID 格式不正确", "code": "INVALID_CONVERSATION_ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        query = str(request.data.get("query", "")).strip()
        if not query:
            return Response(
                {"detail": "请输入要提问的内容", "code": "EMPTY_QUERY"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            saved = get_user_config(request.user)
            config = normalize_config(request.data, saved)
        except ValueError as exc:
            return Response(
                {"detail": str(exc), "code": "INVALID_RAG_CONFIG"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        requested_user_id = str(request.data.get("userMessageId") or "").strip()
        requested_assistant_id = str(request.data.get("assistantMessageId") or "").strip()
        if requested_user_id and not _valid_id(requested_user_id):
            return Response(
                {"detail": "用户消息 ID 格式不正确", "code": "INVALID_MESSAGE_ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if requested_assistant_id and not _valid_id(requested_assistant_id):
            return Response(
                {"detail": "助手消息 ID 格式不正确", "code": "INVALID_MESSAGE_ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = Conversation.objects.filter(id=conversation_id).first()
        if existing and existing.user_id != request.user.id:
            return Response(
                {"detail": "无权访问该会话", "code": "CONVERSATION_CONFLICT"},
                status=status.HTTP_409_CONFLICT,
            )

        requested_title = str(request.data.get("conversationTitle") or "").strip()[:120]
        if existing:
            conversation = existing
            if (
                requested_title
                and conversation.title in {"", DEFAULT_TITLE}
                and requested_title != DEFAULT_TITLE
            ):
                conversation.title = requested_title
                conversation.save(update_fields=["title", "updated_at"])
        else:
            conversation = Conversation.objects.create(
                id=conversation_id,
                user=request.user,
                title=requested_title or _title_from_query(query),
            )

        user_message_id = requested_user_id or _new_id("msg")
        existing_message = Message.objects.filter(id=user_message_id).first()
        if existing_message:
            if (
                existing_message.conversation_id != conversation.id
                or existing_message.role != "user"
            ):
                return Response(
                    {"detail": "消息 ID 冲突", "code": "MESSAGE_CONFLICT"},
                    status=status.HTTP_409_CONFLICT,
                )
            user_message = existing_message
        else:
            user_message = Message.objects.create(
                id=user_message_id,
                conversation=conversation,
                role="user",
                content=query,
                status="done",
            )

        assistant_message_id = requested_assistant_id or _new_id("msg")
        existing_assistant = Message.objects.filter(id=assistant_message_id).first()
        if existing_assistant:
            if existing_assistant.conversation_id != conversation.id or existing_assistant.role != "assistant":
                return Response(
                    {"detail": "助手消息 ID 冲突", "code": "MESSAGE_CONFLICT"},
                    status=status.HTTP_409_CONFLICT,
                )
            existing_assistant.delete()
        assistant_message = Message.objects.create(
            id=assistant_message_id,
            conversation=conversation,
            role="assistant",
            content="",
            status="streaming",
        )
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=["updated_at"])

        history = list(
            conversation.messages.exclude(id__in=[user_message.id, assistant_message.id])
            .order_by("-created_at")[:6]
        )
        history.reverse()
        history_payload = [
            {"role": message.role, "content": message.content}
            for message in history
            if message.content
        ]

        save_user_config(request.user, config)
        stream = run_agent_stream(
            user=request.user,
            conversation=conversation,
            user_message=user_message,
            assistant_message=assistant_message,
            query=query,
            config=config,
            request_id=uuid.uuid4().hex,
            history=history_payload,
        )
        response = StreamingHttpResponse(
            stream,
            content_type="text/event-stream; charset=utf-8",
        )
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response
