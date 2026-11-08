from django.urls import path

from .views import (
    AgentStreamView,
    ConversationClearView,
    ConversationDetailView,
    ConversationListCreateView,
    MessageDeleteView,
)

urlpatterns = [
    path("conversations/", ConversationListCreateView.as_view(), name="conversation-list-create"),
    path(
        "conversations/<str:conversation_id>/messages/",
        ConversationClearView.as_view(),
        name="conversation-clear",
    ),
    path(
        "conversations/<str:conversation_id>/stream/",
        AgentStreamView.as_view(),
        name="agent-stream",
    ),
    path(
        "conversations/<str:conversation_id>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path("messages/<str:message_id>/", MessageDeleteView.as_view(), name="message-delete"),
]
