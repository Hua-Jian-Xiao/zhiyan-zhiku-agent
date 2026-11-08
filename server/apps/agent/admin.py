from django.contrib import admin

from .models import AgentRun, AgentStep, Citation, Conversation, Message, ToolCall


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "updated_at")
    search_fields = ("id", "title", "user__username")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "status", "created_at", "latency_ms")


class StepInline(admin.TabularInline):
    model = AgentStep
    extra = 0


class ToolInline(admin.TabularInline):
    model = ToolCall
    extra = 0


class CitationInline(admin.TabularInline):
    model = Citation
    extra = 0


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "status", "provider", "model", "latency_ms", "started_at")
    list_filter = ("status", "provider", "retrieval_mode")
    inlines = [StepInline, ToolInline, CitationInline]
