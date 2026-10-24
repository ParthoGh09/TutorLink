from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('', views.rate_tutor_view, name='rate_tutor'),
    path('rate/<int:tutor_id>/', views.rate_tutor_view, name='rate_specific_tutor'),
    path('history/', views.review_history_view, name='review_history'),
]
