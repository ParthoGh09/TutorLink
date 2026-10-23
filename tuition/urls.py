from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("applications/", views.applications, name="applications"),
    path("applications/<int:pk>/<str:action>/", views.application_action, name="application_action"),
    path("demo-class/", views.demo_class, name="demo_class"),
    path("demo-class/<int:pk>/", views.demo_class, name="demo_class"),
    path("demo-class/<int:pk>/<str:action>/", views.demo_action, name="demo_action"),
]
