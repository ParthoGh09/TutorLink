from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        TUTOR = 'TUTOR', 'Tutor'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=20, blank=True)

    # Common location details (Area level stays public; exact address remains hidden)
    division = models.CharField(max_length=50, blank=True)
    district = models.CharField(max_length=50, blank=True)
    area = models.CharField(max_length=100, blank=True)

    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

    # Student-specific fields
    institution = models.CharField(max_length=150, blank=True)
    academic_level = models.CharField(max_length=50, blank=True)
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"