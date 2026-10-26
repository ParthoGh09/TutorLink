from django.conf import settings
from django.db import models


class TuitionPost(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    subject = models.CharField(max_length=100)
    class_level = models.CharField(max_length=50)
    description = models.TextField()

    budget_min = models.PositiveIntegerField()
    budget_max = models.PositiveIntegerField()

    division = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    area = models.CharField(max_length=100)

    preferred_days = models.CharField(max_length=100)
    time_slot = models.CharField(max_length=100)

    teaching_mode = models.CharField(
        max_length=20,
        choices=[
            ("ONLINE", "Online"),
            ("OFFLINE", "Offline"),
        ],
        default="ONLINE",
    )

    # Optional picture
    image = models.ImageField(
        upload_to="tuition_posts/",
        blank=True,
        null=True
    )

    status = models.CharField(max_length=20, default="OPEN")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.class_level}"