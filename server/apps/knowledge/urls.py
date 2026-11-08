from django.urls import path

from .views import (
    CourseListView,
    DocumentChunkListView,
    DocumentDetailView,
    DocumentListCreateView,
    DocumentReindexView,
    GraphView,
    KnowledgePointDetailView,
    KnowledgePointListView,
    OverviewView,
)

urlpatterns = [
    path("knowledge-base/overview/", OverviewView.as_view(), name="knowledge-overview"),
    path("courses/", CourseListView.as_view(), name="course-list"),
    path("knowledge-points/", KnowledgePointListView.as_view(), name="knowledge-point-list"),
    path(
        "knowledge-points/<str:uid>/",
        KnowledgePointDetailView.as_view(),
        name="knowledge-point-detail",
    ),
    path("graph/", GraphView.as_view(), name="graph-data"),
    path("documents/", DocumentListCreateView.as_view(), name="document-list-create"),
    path("documents/<str:uid>/", DocumentDetailView.as_view(), name="document-detail"),
    path("documents/<str:uid>/reindex/", DocumentReindexView.as_view(), name="document-reindex"),
    path("documents/<str:uid>/chunks/", DocumentChunkListView.as_view(), name="document-chunks"),
]
