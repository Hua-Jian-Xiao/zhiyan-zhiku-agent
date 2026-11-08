from rest_framework import serializers

from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="username")
    displayName = serializers.CharField(source="display_name")
    avatarText = serializers.CharField(source="avatar_text")

    class Meta:
        model = User
        fields = ("id", "username", "displayName", "role", "avatarText")
