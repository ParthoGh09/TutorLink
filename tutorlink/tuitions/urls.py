
from django.urls import path
from . import views

app_name = "tuitions"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("create/", views.create_post, name="create_post"),
    path("<int:pk>/edit/", views.edit_post, name="edit_post"),
    path("<int:pk>/delete/", views.delete_post, name="delete_post"),
]
