from django.urls import path
from . import views

urlpatterns = [
    path('', views.find_tutors, name='find_tutors'),
]