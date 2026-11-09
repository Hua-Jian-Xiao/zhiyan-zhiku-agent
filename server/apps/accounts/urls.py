from django.urls import path

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    ProfileView,
    RefreshView,
    RegisterView,
    ResetPasswordView,
    SecurityQuestionView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("profile/", ProfileView.as_view(), name="auth-profile"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path(
        "security-question/",
        SecurityQuestionView.as_view(),
        name="auth-security-question",
    ),
    path("reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
]
