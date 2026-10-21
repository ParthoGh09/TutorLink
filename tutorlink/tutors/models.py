from django.conf import settings
from django.db import models

class Subject(models.Model):
    name = models.CharField(max_length=60, unique=True)
    def __str__(self):
        return self.name


class TutorProfile(models.Model):
    class Mode(models.TextChoices):
        ONLINE = 'ONLINE', 'Online'
        OFLINE = 'OFLINE', 'Ofline'
        BOTH = 'BOTH', 'Online + Offline'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tutor_profile')
    uneversity = models.CharField(max_length=150, blank=True)
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




