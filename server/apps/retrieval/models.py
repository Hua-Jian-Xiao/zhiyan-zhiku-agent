from django.conf import settings
from django.db import models

from apps.knowledge.models import DocumentChunk


class RagSettings(models.Model):
    MODE_CHOICES = [
        ("hybrid", "hybrid"),
        ("vector", "vector"),
        ("keyword", "keyword"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rag_settings"
    )
    top_k = models.PositiveSmallIntegerField(default=5)
    threshold = models.FloatField(default=0.72)
    retrieval_mode = models.CharField(max_length=12, choices=MODE_CHOICES, default="hybrid")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rag_settings"


class RetrievalLog(models.Model):
    SOURCE_CHOICES = [
        ("agent", "agent"),
        ("rag_debug", "rag_debug"),
        ("api", "api"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="retrieval_logs"
    )
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default="api")
    conversation_uid = models.CharField(max_length=64, blank=True, default="")
    message_uid = models.CharField(max_length=64, blank=True, default="")
    query = models.TextField()
    retrieval_mode = models.CharField(max_length=12, default="hybrid")
    top_k = models.PositiveSmallIntegerField(default=5)
    threshold = models.FloatField(default=0.72)
    candidate_count = models.IntegerField(default=0)
    result_count = models.IntegerField(default=0)
    embedding_ms = models.IntegerField(default=0)
    search_ms = models.IntegerField(default=0)
    rerank_ms = models.IntegerField(default=0)
    total_ms = models.IntegerField(default=0)
    embedding_provider = models.CharField(max_length=32, default="local")
    embedding_dim = models.IntegerField(default=0)
    config_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "retrieval_logs"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="rlog_user_time_idx"),
            models.Index(fields=["created_at"], name="rlog_time_idx"),
        ]


class RetrievalLogItem(models.Model):
    log = models.ForeignKey(RetrievalLog, on_delete=models.CASCADE, related_name="items")
    chunk = models.ForeignKey(
        DocumentChunk, null=True, blank=True, on_delete=models.SET_NULL, related_name="retrieval_items"
    )
    rank = models.PositiveIntegerField()
    dense_score = models.FloatField(default=0)
    lexical_score = models.FloatField(default=0)
    final_score = models.FloatField(default=0)
    chunk_uid = models.CharField(max_length=80)
    snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "retrieval_log_items"
        ordering = ["log_id", "rank"]
        constraints = [
            models.UniqueConstraint(fields=["log", "rank"], name="uniq_retrieval_log_rank")
        ]
