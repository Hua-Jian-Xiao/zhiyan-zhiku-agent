from django.contrib import admin

from .models import RagSettings, RetrievalLog, RetrievalLogItem


@admin.register(RagSettings)
class RagSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "top_k", "threshold", "retrieval_mode", "updated_at")


class RetrievalLogItemInline(admin.TabularInline):
    model = RetrievalLogItem
    extra = 0
    readonly_fields = ("rank", "chunk_uid", "dense_score", "lexical_score", "final_score")


@admin.register(RetrievalLog)
class RetrievalLogAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "user", "query", "retrieval_mode", "result_count", "total_ms", "created_at")
    list_filter = ("source", "retrieval_mode")
    inlines = [RetrievalLogItemInline]
