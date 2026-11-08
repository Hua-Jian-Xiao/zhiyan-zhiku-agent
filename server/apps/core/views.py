from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .stats import health_payload, public_stats


class PublicStatsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(public_stats())


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(health_payload())


class ApiRootView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "name": "智研知库 RAG-Agent API",
                "version": "v1",
                "docs": "See README.md",
                "health": "/api/v1/health/",
            }
        )
