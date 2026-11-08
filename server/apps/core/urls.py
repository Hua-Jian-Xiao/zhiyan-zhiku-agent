from django.urls import path

from .views import ApiRootView, HealthView, PublicStatsView

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
    path("health/", HealthView.as_view(), name="health"),
    path("public/stats/", PublicStatsView.as_view(), name="public-stats"),
]
