from django.urls import path

from . import views

app_name = "tuition"

urlpatterns = [
    # Screen 09 – student
    path("posts/create/", views.create_post, name="create_post"),
    path("posts/mine/", views.my_posts, name="my_posts"),
    path("posts/<int:pk>/status/", views.change_status, name="change_status"),
    # Screen 10 – tutor
    path("find/", views.find_tuition, name="find_tuition"),
    path("posts/<int:pk>/save/", views.toggle_save, name="toggle_save"),
    # Screen 11 – student + tutor
    path("posts/<int:pk>/", views.post_detail, name="post_detail"),
    path("posts/<int:pk>/apply/", views.apply, name="apply"),
    path("posts/<int:pk>/comment/", views.add_comment, name="add_comment"),
    path("comments/<int:pk>/edit/", views.edit_comment, name="edit_comment"),
    path("comments/<int:pk>/delete/", views.delete_comment, name="delete_comment"),
]
