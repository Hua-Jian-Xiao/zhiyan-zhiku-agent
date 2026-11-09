from pathlib import Path

from rest_framework import serializers

from .models import User

ALLOWED_AVATAR_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024


class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="username")
    displayName = serializers.CharField(source="display_name")
    avatarText = serializers.CharField(source="avatar_text")
    avatarUrl = serializers.SerializerMethodField()
    securityQuestion = serializers.CharField(source="security_question")
    hasSecurityQuestion = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "displayName",
            "role",
            "avatarText",
            "avatarUrl",
            "email",
            "major",
            "grade",
            "bio",
            "securityQuestion",
            "hasSecurityQuestion",
        )

    def get_avatarUrl(self, obj: User) -> str:
        return obj.avatar.url if obj.avatar else ""

    def get_hasSecurityQuestion(self, obj: User) -> bool:
        return bool(obj.security_question and obj.security_answer_hash)


class ProfileUpdateSerializer(serializers.Serializer):
    displayName = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    major = serializers.CharField(max_length=120, required=False, allow_blank=True)
    grade = serializers.CharField(max_length=40, required=False, allow_blank=True)
    bio = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    securityQuestion = serializers.CharField(
        max_length=160, required=False, allow_blank=True
    )
    securityAnswer = serializers.CharField(
        max_length=120, required=False, allow_blank=True, write_only=True
    )
    avatar = serializers.FileField(required=False, allow_null=True)

    def validate_displayName(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("昵称不能为空")
        return cleaned

    def validate_avatar(self, value):
        if value is None:
            return value
        if value.size > MAX_AVATAR_BYTES:
            raise serializers.ValidationError("头像不能超过 2 MB")
        extension = Path(value.name).suffix.lower()
        if extension not in ALLOWED_AVATAR_EXTENSIONS:
            raise serializers.ValidationError("仅支持 PNG、JPG、JPEG、WEBP、GIF 图片")
        if value.content_type and not value.content_type.startswith("image/"):
            raise serializers.ValidationError("上传文件必须是图片")
        return value

    def validate(self, attrs):
        has_question = "securityQuestion" in attrs
        has_answer = "securityAnswer" in attrs
        if has_question or has_answer:
            question = (attrs.get("securityQuestion") or "").strip()
            answer = (attrs.get("securityAnswer") or "").strip()
            if not question or not answer:
                raise serializers.ValidationError(
                    "设置安全问题需要同时填写问题和答案"
                )
            if len(answer) < 2:
                raise serializers.ValidationError("安全问题答案至少需要 2 个字符")
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    oldPassword = serializers.CharField()
    newPassword = serializers.CharField(min_length=6)

    def validate(self, attrs):
        if attrs["oldPassword"] == attrs["newPassword"]:
            raise serializers.ValidationError("新密码不能与当前密码相同")
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()
    answer = serializers.CharField()
    newPassword = serializers.CharField(min_length=6)
