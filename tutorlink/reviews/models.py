from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

RATING_VALIDATORS = [MinValueValidator(1), MaxValueValidator(5)]

class Tuition(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tuitions_as_student")
    tutor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tuitions_as_tutor")
    subject = models.CharField(max_length=80)
    class_level = models.CharField(max_length=40, blank=True)
    started_on = models.DateField(default=timezone.localdate)
    ended_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-started_on"]

    def __str__(self):
        return f"{self.subject} ({self.student} - {self.tutor})"

    @property
    def is_confirmed(self):
        return self.status == self.Status.CONFIRMED

    @property
    def period_label(self):
        start = self.started_on.strftime("%b")
        end = (self.ended_on or self.started_on).strftime("%b %Y")
        return f"{start}–{end}" if start != end.split()[0] else end

    @property
    def title(self):
        return f"{self.subject} · {self.class_level}" if self.class_level else self.subject

    def other_party(self, user):
        if user.pk == self.student_id:
            return self.tutor
        if user.pk == self.tutor_id:
            return self.student
        return None


class Review(models.Model):
    tuition = models.ForeignKey(Tuition, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_written")
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_received")

    overall_rating = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    subject_knowledge = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    communication = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    punctuality = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)
    safety_respect = models.PositiveSmallIntegerField(validators=RATING_VALIDATORS)

    comment = models.TextField(blank=True)
    is_verified_post = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    CRITERIA = [
        ("subject_knowledge", "Subject knowledge"),
        ("communication", "Communication"),
        ("punctuality", "Punctuality"),
        ("safety_respect", "Safety & respect"),
    ]

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["tuition", "reviewer"], name="one_review_per_reviewer_per_tuition"),
            models.CheckConstraint(condition=~Q(reviewer=models.F("reviewee")), name="no_self_review"),
        ]

    def __str__(self):
        return f"{self.reviewer} -> {self.reviewee}: {self.overall_rating}"

    def clean(self):
        if self.tuition_id and not self.tuition.is_confirmed:
            raise ValidationError("You can review only after the tuition is confirmed.")
