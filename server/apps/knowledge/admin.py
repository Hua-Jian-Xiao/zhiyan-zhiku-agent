from django.contrib import admin

from .models import (
    Course,
    Document,
    DocumentChunk,
    GraphCategory,
    GraphEdge,
    GraphNode,
    KnowledgePoint,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("uid", "name", "code", "teacher", "sort_order")
    search_fields = ("uid", "name", "code")


@admin.register(KnowledgePoint)
class KnowledgePointAdmin(admin.ModelAdmin):
    list_display = ("uid", "name", "course", "chapter", "difficulty")
    list_filter = ("course", "difficulty")
    search_fields = ("uid", "name")


@admin.register(GraphCategory)
class GraphCategoryAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "color", "sort_order")


@admin.register(GraphNode)
class GraphNodeAdmin(admin.ModelAdmin):
    list_display = ("uid", "name", "category", "difficulty")
    list_filter = ("category",)


@admin.register(GraphEdge)
class GraphEdgeAdmin(admin.ModelAdmin):
    list_display = ("source", "target", "relation", "weight")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("uid", "title", "course", "status", "chunk_count", "updated_at")
    list_filter = ("course", "status")
    search_fields = ("uid", "title", "original_filename")


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("uid", "title", "course", "knowledge_point", "embedding_dim")
    list_filter = ("course", "embedding_provider")
    search_fields = ("uid", "title", "content")
