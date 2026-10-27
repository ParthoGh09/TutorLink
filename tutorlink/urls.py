from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("tuition.urls")),
    path("notifications/", include("notifications.urls")),
    path("reviews/", include("reviews.urls")),
]
