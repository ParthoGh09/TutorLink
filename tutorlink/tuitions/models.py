
from django.conf import settings
from django.db import models


class TuitionPost(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    target_tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="targeted_tuition_posts",
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
    image = models.ImageField(
        upload_to="tuition_posts/",
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, default="OPEN")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.class_level}"


class TuitionApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    tuition = models.ForeignKey(
        TuitionPost,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tuition_applications",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    review_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )
    review_text = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tuition", "tutor"],
                name="unique_tutor_application_per_tuition",
            )
        ]

    def __str__(self):
        return f"{self.tutor} - {self.tuition}"
