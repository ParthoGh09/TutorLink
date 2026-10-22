from django.conf import settings
from django.db import models


class Subject(models.Model):
    name = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.name


class TutorProfile(models.Model):
    class Mode(models.TextChoices):
        ONLINE = 'ONLINE', 'Online'
        OFFLINE = 'OFFLINE', 'Offline'
        BOTH = 'BOTH', 'Online + Offline'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tutor_profile'
    )
    university = models.CharField(max_length=150, blank=True)
    department = models.CharField(max_length=100, blank=True)
    subjects = models.ManyToManyField(Subject, blank=True, related_name='tutors')
    class_from = models.PositiveSmallIntegerField(default=6)
    class_to = models.PositiveSmallIntegerField(default=12)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.BOTH)
    experience_years = models.PositiveSmallIntegerField(default=0)
    available_time = models.CharField(max_length=80, blank=True)  # e.g. "Sat-Thu, 4-9 PM"

    # Temporary values until a Review model exists
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    review_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Tutor profile: {self.user.username}"

class DemoClass(models.Model):
    class Platform(models.TextChoices):
        MEET = 'MEET', 'Google Meet'
        ZOOM = 'ZOOM', 'Zoom'

    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Requested'
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='demo_requests'
    )
    tutor = models.ForeignKey(TutorProfile, on_delete=models.CASCADE, related_name='demo_classes')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    platform = models.CharField(max_length=10, choices=Platform.choices, default=Platform.MEET)
    meeting_link = models.URLField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'tutor'], name='one_demo_per_student_tutor'),
        ]

    def __str__(self):
        return f"Demo: {self.student.username} with {self.tutor.user.username} ({self.status})"


