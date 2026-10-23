from django.urls import path
from . import views

urlpatterns = [
    path('', views.find_tutors, name='find_tutors'),
    path('<int:pk>/', views.tutor_profile, name='tutor_profile'),
]