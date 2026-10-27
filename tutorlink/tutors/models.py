
from django.conf import settings
from django.db import models


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TutorProfile(models.Model):
    class Mode(models.TextChoices):
        ONLINE = "ONLINE", "Online"
        OFFLINE = "OFFLINE", "Offline"
        BOTH = "BOTH", "Online & Offline"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutor_profile",
    )
    university = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200, blank=True)
    subjects = models.ManyToManyField(
        Subject,
        blank=True,
        related_name="tutors",
    )
    class_from = models.PositiveSmallIntegerField(default=1)
    class_to = models.PositiveSmallIntegerField(default=12)
    expected_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    mode = models.CharField(
        max_length=20,
        choices=Mode.choices,
        default=Mode.BOTH,
    )
    experience_years = models.PositiveSmallIntegerField(default=0)
    available_time = models.CharField(max_length=200, blank=True)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
    )
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-rating", "-review_count"]

    def __str__(self):
        return (
            f"Tutor Profile - "
            f"{self.user.get_full_name() or self.user.username}"
        )

    @property
    def has_expected_salary(self):
        return self.expected_salary > 0


class DemoClass(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    # Connect each demo to its exact tuition application.
    # Nullable to preserve existing demo records.
    application = models.OneToOneField(
        "tuitions.TuitionApplication",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="demo_class",
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_demo_classes",
    )
    tutor = models.ForeignKey(
        TutorProfile,
        on_delete=models.CASCADE,
        related_name="demo_classes",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demo_classes",
    )
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    platform = models.CharField(max_length=50, blank=True)
    meeting_link = models.URLField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Demo: {self.student} - {self.tutor.user} - "
            f"{self.subject or 'Subject not set'}"
        )
