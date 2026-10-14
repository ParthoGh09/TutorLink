from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('notifications/', include('notifications.urls')),
    path('reviews/', include('reviews.urls')),
    path('', RedirectView.as_view(pattern_name='notifications:list', permanent=False)),
]