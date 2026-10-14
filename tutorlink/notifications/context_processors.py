def unread_notifications(request):
    user = request.user
    if not user.is_authenticated:
        return {"unread_notification_count": 0}

    from .models import Notification

    count = Notification.objects.filter(user=user, is_read=False).count()
    return {"unread_notification_count": count}