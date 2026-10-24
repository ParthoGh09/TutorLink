from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class NotificationType(models.TextChoices):
    MATCH = 'MATCH', 'Match'
    APPLICATION = 'APPLICATION', 'Application'
    DEMO = 'DEMO', 'Demo'
    VERIFICATION = 'VERIFICATION', 'Verification'
    LOCATION = 'LOCATION', 'Location'
    REVIEW = 'REVIEW', 'Review'
    SYSTEM = 'SYSTEM', 'System'


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
