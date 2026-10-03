from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        TUTOR = 'TUTOR', 'Tutor'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=20, blank=True)

    division = models.CharField(max_length=50, blank=True)
    district = models.CharField(max_length=50, blank=True)
    area = models.CharField(max_length=100, blank=True)

    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

    # Student specific fields
    institution = models.CharField(max_length=150, blank=True)
    academic_level = models.CharField(max_length=50, blank=True)
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class VerificationDocument(models.Model):
    class DocType(models.TextChoices):
        ID_CARD = 'ID_CARD', 'ID Card'
        STUDENT_ID = 'STUDENT_ID', 'Student ID'
        CERTIFICATE = 'CERTIFICATE', 'Certificate'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=20, choices=DocType.choices, default=DocType.STUDENT_ID)
    file = models.FileField(upload_to='verifications/')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_doc_type_display()} ({self.status})"