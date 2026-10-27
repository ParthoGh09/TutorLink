from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class NotificationType(models.TextChoices):
    MATCH = 'MATCH'
    APPLICATION = 'APPLICATION'
    DEMO = 'DEMO'
    VERIFICATION = 'VERIFICATION'
    LOCATION = 'LOCATION'
    REVIEW = 'REVIEW'
    SYSTEM = 'SYSTEM'


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['is_read', '-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title} to {self.recipient.username}"

    def mark_as_read(self):
        """Class diagram mapped method: mark_as_read()"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    @property
    def time_ago(self):
        """Returns relative time string matching Slide 17 UI (5m, 40m, 2h, Yesterday, Mon, Oct 20)."""
        now = timezone.now()
        diff = now - self.created_at
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m"
        elif seconds < 86400:
            return f"{int(seconds // 3600)}h"
        elif seconds < 172800:
            return "Yesterday"
        elif seconds < 604800: # Within 7 days
            return self.created_at.strftime("%a") # e.g. Mon, Tue
        else:
            return self.created_at.strftime("%b %d") # e.g. Oct 20

    @property
    def icon_symbol(self):
        icons = {
            NotificationType.MATCH: "✦",
            NotificationType.APPLICATION: "👥",
            NotificationType.DEMO: "📹",
            NotificationType.VERIFICATION: "🛡️",
            NotificationType.LOCATION: "🎯",
            NotificationType.REVIEW: "⭐",
            NotificationType.SYSTEM: "🔔",
        }
        return icons.get(self.notification_type, "🔔")
