from django.conf import settings
from django.db import models

from apps.knowledge.models import DocumentChunk
from apps.retrieval.models import RetrievalLog


class Conversation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations"
    )
    title = models.CharField(max_length=120, default="新的学习会话")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversations"
        ordering = ["-updated_at", "-created_at"]
        indexes = [
            models.Index(fields=["user", "-updated_at"], name="conv_user_updated_idx"),
        ]


class Message(models.Model):
    ROLE_CHOICES = [("user", "user"), ("assistant", "assistant")]
    STATUS_CHOICES = [
        ("streaming", "streaming"),
        ("done", "done"),
        ("error", "error"),
    ]

    id = models.CharField(max_length=64, primary_key=True)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=12, choices=ROLE_CHOICES)
    content = models.TextField(blank=True, default="")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="done")
    created_at = models.DateTimeField(auto_now_add=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    stopped = models.BooleanField(default=False)
    error = models.TextField(blank=True, default="")

    class Meta:
        db_table = "messages"
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["conversation", "created_at"], name="msg_conv_time_idx"),
        ]


class AgentRun(models.Model):
    STATUS_CHOICES = [
        ("running", "running"),
        ("done", "done"),
        ("error", "error"),
        ("stopped", "stopped"),
    ]

    id = models.CharField(max_length=64, primary_key=True)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="runs"
    )
    message = models.OneToOneField(
        Message, on_delete=models.CASCADE, related_name="agent_run"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_runs"
    )
    query = models.TextField()
    top_k = models.PositiveSmallIntegerField(default=5)
    threshold = models.FloatField(default=0.72)
    retrieval_mode = models.CharField(max_length=12, default="hybrid")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="running")
    provider = models.CharField(max_length=20, default="local")
    model = models.CharField(max_length=64, blank=True, default="")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    cited_count = models.IntegerField(default=0)
    retrieval_snapshot = models.JSONField(default=list, blank=True)
    config_snapshot = models.JSONField(default=dict, blank=True)
    retrieval_log = models.ForeignKey(
        RetrievalLog, null=True, blank=True, on_delete=models.SET_NULL, related_name="agent_runs"
    )
    error = models.TextField(blank=True, default="")

    class Meta:
        db_table = "agent_runs"
        ordering = ["-started_at", "-id"]
        indexes = [
            models.Index(fields=["conversation", "started_at"], name="run_conv_time_idx"),
        ]


class AgentStep(models.Model):
    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="steps")
    step_key = models.CharField(max_length=32)
    title = models.CharField(max_length=80)
    detail = models.TextField(blank=True, default="")
    status = models.CharField(max_length=12, default="pending")
    duration_ms = models.IntegerField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "agent_steps"
        ordering = ["run_id", "sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["run", "step_key"], name="uniq_run_step")
        ]


class ToolCall(models.Model):
    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="tools")
    call_key = models.CharField(max_length=48)
    name = models.CharField(max_length=80)
    label = models.CharField(max_length=80)
    status = models.CharField(max_length=12, default="running")
    input_text = models.TextField(blank=True, default="")
    output_text = models.TextField(blank=True, default="")
    duration_ms = models.IntegerField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "agent_tool_calls"
        ordering = ["run_id", "sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["run", "call_key"], name="uniq_run_tool")
        ]


class Citation(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="citations")
    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="citations")
    chunk = models.ForeignKey(
        DocumentChunk, null=True, blank=True, on_delete=models.SET_NULL, related_name="citations"
    )
    index_no = models.PositiveIntegerField()
    knowledge_point_uid = models.CharField(max_length=64)
    title = models.CharField(max_length=200)
    course_name = models.CharField(max_length=128)
    source_name = models.CharField(max_length=255)
    chapter = models.CharField(max_length=160, blank=True, default="")
    snippet = models.TextField()
    score = models.FloatField(default=0)

    class Meta:
        db_table = "citations"
        ordering = ["message_id", "index_no"]
        constraints = [
            models.UniqueConstraint(fields=["message", "index_no"], name="uniq_message_citation")
        ]
