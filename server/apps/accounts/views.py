import re
import time

from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserProfileSerializer

USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{2,32}$")


def issue_tokens(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "token": str(refresh.access_token),
        "refresh": str(refresh),
        "signedAt": int(time.time() * 1000),
        "user": UserProfileSerializer(user).data,
    }


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", ""))
        if not username or not password:
            return Response(
                {"detail": "请输入账号和密码", "code": "INVALID_CREDENTIALS"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = authenticate(request, username=username, password=password)
        if user is None or not user.is_active:
            return Response(
                {"detail": "账号或密码不正确", "code": "INVALID_CREDENTIALS"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return Response(issue_tokens(user))


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", ""))
        display_name = str(request.data.get("displayName", "")).strip()[:50]

        if not USERNAME_RE.fullmatch(username):
            return Response(
                {
                    "detail": "账号需为 2-32 位字母、数字、下划线或短横线",
                    "code": "INVALID_USERNAME",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(password) < 6:
            return Response(
                {"detail": "密码至少需要 6 位", "code": "INVALID_PASSWORD"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username__iexact=username).exists():
            return Response(
                {"detail": "该账号已存在，请直接登录", "code": "USERNAME_EXISTS"},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password)
                user.display_name = display_name or username
                user.role = "计算机科学 · 学习者"
                user.avatar_text = user.display_name[:1].upper()
                user.last_login = timezone.now()
                user.save(update_fields=["display_name", "role", "avatar_text", "last_login"])
        except IntegrityError:
            return Response(
                {"detail": "该账号已存在，请直接登录", "code": "USERNAME_EXISTS"},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(issue_tokens(user), status=status.HTTP_201_CREATED)


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_value = request.data.get("refresh")
        if not refresh_value:
            return Response(
                {"detail": "缺少刷新令牌", "code": "MISSING_REFRESH"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = TokenRefreshSerializer(data={"refresh": refresh_value})
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                "token": serializer.validated_data["access"],
                "refresh": refresh_value,
            }
        )


class MeView(APIView):
    def get(self, request):
        return Response({"user": UserProfileSerializer(request.user).data})


class LogoutView(APIView):
    def post(self, request):
        # The demo intentionally keeps tokens stateless; the client discards them.
        return Response(status=status.HTTP_204_NO_CONTENT)
