from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("verify/", views.verify_identity_view, name="verify_identity"),
    path("dashboard/", views.role_dashboard, name="role_dashboard"),
    path("student/", views.student_dashboard, name="student_dashboard"),
    path("tutor/", views.tutor_dashboard, name="tutor_dashboard"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("logout/", views.logout_view, name="logout"),
]