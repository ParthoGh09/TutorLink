from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
      ADMIN = "ADMIN", "Administrator"
      TUTOR = "TUTOR", "Tutor"
      STUDENT = "STUDENT", "Student"


class User(AbstractUser):
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    area = models.CharField(max_length=100, blank=True)
    institution = models.CharField(max_length=150, blank=True)
    is_verified = models.BooleanField(default=False)

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def is_tutor(self):
        return self.role == Role.TUTOR

    @property
    def is_student(self):
        return self.role == Role.STUDENT

    def __str__(self):
        return f"{self.display_name} ({self.get_role_display()})"