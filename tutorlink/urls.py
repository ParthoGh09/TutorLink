from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def index_redirect(_request):
    """Direct root URL (127.0.0.1:8000) directly to Notifications (Slide 17)."""
    return redirect("notifications:notification_list")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index_redirect, name="index_redirect"),
    path("notifications/", include("notifications.urls")),
    path("reviews/", include("reviews.urls")),
    path("tuition/", include("tuition.urls")),
]
