from django.urls import path
from . import views

app_name = "tuitions"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("create/", views.create_post, name="create_post"),
    path("applications/", views.applications, name="applications"),
    path("demo-classes/", views.demo_classes, name="demo_classes"),

    path(
        "applications/<int:application_id>/accept/",
        views.accept_application,
        name="accept_application",
    ),
    path(
        "applications/<int:application_id>/reject/",
        views.reject_application,
        name="reject_application",
    ),
    path(
        "applications/<int:application_id>/schedule-demo/",
        views.schedule_demo,
        name="schedule_demo",
    ),
    path(
        "applications/<int:application_id>/demo/",
        views.demo_detail,
        name="demo_detail",
    ),
    path(
        "applications/<int:application_id>/complete-demo/",
        views.complete_demo,
        name="complete_demo",
    ),
    path(
        "applications/<int:application_id>/confirm-tutor/",
        views.confirm_tutor,
        name="confirm_tutor",
    ),
    path(
        "applications/<int:application_id>/decline-tutor/",
        views.decline_tutor,
        name="decline_tutor",
    ),
    path(
        "applications/<int:application_id>/review/",
        views.submit_review,
        name="submit_review",
    ),

    path("<int:pk>/", views.post_detail, name="post_detail"),
    path("<int:pk>/edit/", views.edit_post, name="edit_post"),
    path("<int:pk>/delete/", views.delete_post, name="delete_post"),
    path("<int:pk>/apply/", views.apply_for_tuition, name="apply"),
    path(
        "<int:pk>/apply/",
        views.apply_for_tuition,
        name="apply_for_tuition",
    ),
]