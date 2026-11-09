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
from .serializers import (
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
)

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


class ProfileView(APIView):
    def get(self, request):
        return Response({"user": UserProfileSerializer(request.user).data})

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user
        update_fields: list[str] = []

        if "displayName" in data:
            user.display_name = data["displayName"].strip()
            user.avatar_text = (user.display_name[:1] or user.username[:1]).upper()
            update_fields.extend(["display_name", "avatar_text"])
        if "email" in data:
            user.email = data["email"].strip()
            update_fields.append("email")
        if "major" in data:
            user.major = data["major"].strip()
            update_fields.append("major")
        if "grade" in data:
            user.grade = data["grade"].strip()
            update_fields.append("grade")
        if "bio" in data:
            user.bio = data["bio"].strip()
            update_fields.append("bio")
        if "securityQuestion" in data:
            user.security_question = data["securityQuestion"].strip()
            user.set_security_answer(data["securityAnswer"])
            update_fields.extend(["security_question", "security_answer_hash"])

        old_avatar = user.avatar if user.avatar and user.avatar.name else None
        avatar = data.get("avatar")
        if avatar is not None:
            user.avatar = avatar
            update_fields.append("avatar")

        if update_fields:
            user.save(update_fields=update_fields)
        if avatar is not None and old_avatar and old_avatar.name != user.avatar.name:
            try:
                old_avatar.delete(save=False)
            except OSError:
                pass

        return Response({"user": UserProfileSerializer(user).data})


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["oldPassword"]):
            return Response(
                {"detail": "当前密码不正确", "code": "INVALID_OLD_PASSWORD"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.set_password(serializer.validated_data["newPassword"])
        request.user.save(update_fields=["password"])
        return Response({"detail": "密码已更新，请使用新密码登录"})


class SecurityQuestionView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        username = str(request.query_params.get("username", "")).strip()
        if not username:
            return Response(
                {"detail": "请输入账号", "code": "MISSING_USERNAME"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.filter(username__iexact=username).first()
        if not user or not user.security_question or not user.security_answer_hash:
            return Response(
                {
                    "detail": "账号不存在或未设置安全问题，请登录后在个人中心设置",
                    "code": "SECURITY_QUESTION_NOT_SET",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "username": user.username,
                "securityQuestion": user.security_question,
            }
        )


class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"].strip()
        user = User.objects.filter(username__iexact=username).first()
        if not user or not user.security_answer_hash:
            return Response(
                {
                    "detail": "账号不存在或未设置安全问题",
                    "code": "SECURITY_QUESTION_NOT_SET",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.check_security_answer(serializer.validated_data["answer"]):
            return Response(
                {"detail": "安全问题答案不正确", "code": "INVALID_SECURITY_ANSWER"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["newPassword"])
        user.save(update_fields=["password"])
        return Response({"detail": "密码已重置，请使用新密码登录"})
