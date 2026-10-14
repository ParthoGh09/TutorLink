from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationType(models.TextChoices):
    MATCH = "MATCH", "Match"
    APPLICATION = "APPLICATION", "Application"
    DEMO = "DEMO", "Demo"
    VERIFICATION = "VERIFICATION", "Verification"
    REVIEW = "REVIEW", "Review"
    LOCATION = "LOCATION", "Location"
    SYSTEM = "SYSTEM", "System"


TYPE_ICONS = {
    "MATCH": "✨",
    "APPLICATION": "👥",
    "DEMO": "🎥",
    "VERIFICATION": "🛡️",
    "REVIEW": "⭐",
    "LOCATION": "📍",
    "SYSTEM": "🔔",
}


class NotificationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def unread(self):
        return self.filter(is_read=False)


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=15, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    title = models.CharField(max_length=160)
    message = models.CharField(max_length=300, blank=True)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ["is_read", "-created_at"]

    def __str__(self):
        return f"[{self.type}] {self.title}"

    @property
    def icon(self):
        return TYPE_ICONS.get(self.type, "🔔")

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])