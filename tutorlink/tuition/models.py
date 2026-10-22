import re

from django.conf import settings
from django.db import models
from django.urls import reverse


class TuitionPost(models.Model):
    """Class diagram: TuitionPost (create(), Status {OPEN, CLOSED, PAUSED})."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPEN = "OPEN", "Open"
        PAUSED = "PAUSED", "Paused"
        CLOSED = "CLOSED", "Closed"

    class Mode(models.TextChoices):
        ONLINE = "ONLINE", "Online"
        OFFLINE = "OFFLINE", "Offline"

    class PostType(models.TextChoices):
        NEED = "NEED", "Tuition need"
        EXAM = "EXAM", "Exam preparation"
        GROUP = "GROUP", "Group study"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tuition_posts"
    )
    subject = models.CharField(max_length=60)
    class_level = models.CharField(max_length=40)
    post_type = models.CharField(max_length=10, choices=PostType.choices, default=PostType.NEED)
    budget_min = models.PositiveIntegerField()
    budget_max = models.PositiveIntegerField()

    # Only the area is public. No street address is ever stored on a post.
    division = models.CharField(max_length=60)
    district = models.CharField(max_length=60)
    area = models.CharField(max_length=80)

    preferred_days = models.CharField(max_length=40, help_text="Comma separated, e.g. Sat,Mon,Wed")
    time_slot = models.CharField(max_length=40)
    teaching_mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.ONLINE)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse("tuition:post_detail", args=[self.pk])

    # ---- display helpers -------------------------------------------------
    @property
    def title(self):
        return f"{self.subject} · {self.class_level}"

    @property
    def days_list(self):
        return [d for d in self.preferred_days.split(",") if d]

    @property
    def days_display(self):
        return " · ".join(self.days_list)

    @property
    def budget_display(self):
        if self.budget_min == self.budget_max:
            return f"৳{self.budget_min:,}"
        return f"৳{self.budget_min:,}–{self.budget_max:,}"

    @property
    def location_display(self):
        return f"{self.area}, {self.district}"

    @property
    def time_display(self):
        """'5:00 PM – 7:00 PM' -> '5:00 – 7:00 PM' (shorter, as in the design)."""
        m = re.match(r"^(\S+) (AM|PM) – (\S+) (AM|PM)$", self.time_slot)
        if m and m.group(2) == m.group(4):
            return f"{m.group(1)} – {m.group(3)} {m.group(2)}"
        return self.time_slot

    @property
    def is_online(self):
        return self.teaching_mode == self.Mode.ONLINE

    @property
    def is_open(self):
        return self.status == self.Status.OPEN


class Comment(models.Model):
    """Class diagram: Comment (replies are Comments with a parent)."""

    post = models.ForeignKey(TuitionPost, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tuition_comments"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} on {self.post_id}: {self.body[:30]}"

    @property
    def is_reply(self):
        return self.parent_id is not None


class Application(models.Model):
    """Class diagram: Application (apply(), AppStatus). One per tutor-post pair."""

    class AppStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        DEMO_REQUESTED = "DEMO_REQUESTED", "Demo requested"
        DEMO_SCHEDULED = "DEMO_SCHEDULED", "Demo scheduled"
        DEMO_COMPLETED = "DEMO_COMPLETED", "Demo completed"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    post = models.ForeignKey(TuitionPost, on_delete=models.CASCADE, related_name="applications")
    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tuition_applications"
    )
    message = models.TextField(blank=True)
    match_score = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=AppStatus.choices, default=AppStatus.PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(fields=["post", "tutor"], name="one_application_per_tutor_post")
        ]

    def __str__(self):
        return f"{self.tutor} -> {self.post} [{self.status}]"


class SavedPost(models.Model):
    """Powers the 'Saved Posts' tab on Find Tuition."""

    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_tuition_posts"
    )
    post = models.ForeignKey(TuitionPost, on_delete=models.CASCADE, related_name="saved_by")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-saved_at"]
        constraints = [models.UniqueConstraint(fields=["tutor", "post"], name="unique_saved_post")]
