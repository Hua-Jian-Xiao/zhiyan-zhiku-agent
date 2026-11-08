from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    display_name = models.CharField(max_length=100, blank=True, default="")
    role = models.CharField(max_length=120, blank=True, default="计算机科学 · 学习者")
    avatar_text = models.CharField(max_length=8, blank=True, default="")
    major = models.CharField(max_length=120, blank=True, default="")
    grade = models.CharField(max_length=40, blank=True, default="")
    bio = models.TextField(blank=True, default="")

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
