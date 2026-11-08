from django.urls import path

from .views import RagConfigView, RetrievalQueryView

urlpatterns = [
    path("retrieval/query/", RetrievalQueryView.as_view(), name="retrieval-query"),
    path("rag/config/", RagConfigView.as_view(), name="rag-config"),
]
