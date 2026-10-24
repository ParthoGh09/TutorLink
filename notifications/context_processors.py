from .models import Notification
from django.contrib.auth.models import User


def notifications_unread(request):
    """Provides dynamic unread notifications count across all templates."""
    try:
        user = request.user
        if not user.is_authenticated:
            user = User.objects.filter(username='ayesha_rahman').first()
        if user:
            count = Notification.objects.filter(recipient=user, is_read=False).count()
            return {'unread_notifications_count': count}
    except Exception:
        pass
    return {'unread_notifications_count': 0}
