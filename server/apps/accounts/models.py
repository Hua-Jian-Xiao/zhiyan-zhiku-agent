from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    display_name = models.CharField(max_length=100, blank=True, default="")
    role = models.CharField(max_length=120, blank=True, default="计算机科学 · 学习者")
    avatar_text = models.CharField(max_length=8, blank=True, default="")
    avatar = models.FileField(upload_to="avatars/", blank=True, null=True)
    major = models.CharField(max_length=120, blank=True, default="")
    grade = models.CharField(max_length=40, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    security_question = models.CharField(max_length=160, blank=True, default="")
    security_answer_hash = models.CharField(max_length=128, blank=True, default="")

    def set_security_answer(self, answer: str) -> None:
        normalized = (answer or "").strip().lower()
        self.security_answer_hash = make_password(normalized) if normalized else ""

    def check_security_answer(self, answer: str) -> bool:
        normalized = (answer or "").strip().lower()
        return bool(self.security_answer_hash) and check_password(
            normalized, self.security_answer_hash
        )

    class Meta:
        db_table = "users"
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.username
        if not self.avatar_text:
            self.avatar_text = self.display_name[:1].upper()
        super().save(*args, **kwargs)
