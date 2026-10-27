from django.urls import path
from . import views

urlpatterns = [
    path("", views.find_tutors, name="find_tutors"),
    path(
        "<int:profile_id>/",
        views.tutor_detail,
        name="tutor_detail",
    ),
    path(
        "<int:profile_id>/request/",
        views.request_tutor,
        name="request_tutor",
    ),
]