from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.search import (
    config_payload,
    get_user_config,
    normalize_config,
    perform_retrieval,
    public_retrieval_response,
    save_user_config,
)


class RagConfigView(APIView):
    def get(self, request):
        config = get_user_config(request.user)
        return Response(config_payload(config))

    def put(self, request):
        try:
            current = get_user_config(request.user)
            config = normalize_config(request.data, current)
        except ValueError as exc:
            return Response(
                {"detail": str(exc), "code": "INVALID_RAG_CONFIG"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        save_user_config(request.user, config)
        return Response(config_payload(config))


class RetrievalQueryView(APIView):
    def post(self, request):
        query = str(request.data.get("query", "")).strip()
        try:
            saved = get_user_config(request.user)
            config = normalize_config(request.data, saved)
            result = perform_retrieval(
                query,
                config,
                user=request.user,
                source="rag_debug",
                course_uid=request.data.get("courseId") or None,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc), "code": "INVALID_RETRIEVAL"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(public_retrieval_response(result))
