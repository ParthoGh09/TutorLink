
"""
URL configuration for tutorlink project.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    return redirect("role_dashboard")


urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("tutors/", include("tutors.urls")),

    path("tuitions/", include("tuitions.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
