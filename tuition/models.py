import datetime
from datetime import date, time, timedelta

from django.db import models


class Tutor(models.Model):
    name = models.CharField(max_length=80)
    institution = models.CharField(max_length=120)  # e.g. "EEE · BUET"
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.5)
    expected_fee = models.PositiveIntegerField(default=5000)  # taka / month
    area = models.CharField(max_length=80)  # area only, never exact address
    verified = models.BooleanField(default=True)
    avatar_color = models.CharField(max_length=7, default="#DCE3FF")

    def __str__(self):
        return self.name

    @property
    def initials(self):
        return "".join(w[0] for w in self.name.split()[:2]).upper()


class TuitionPost(models.Model):
    subject = models.CharField(max_length=60)
    class_level = models.CharField(max_length=30)
    student_name = models.CharField(max_length=80, default="Ayesha Rahman")

    def __str__(self):
        return self.title

    @property
    def title(self):
        return f"{self.subject} · {self.class_level}"


class Application(models.Model):
    PENDING = "pending"
    SHORTLISTED = "shortlisted"
    DEMO_REQUESTED = "demo_requested"
    DEMO_SCHEDULED = "demo_scheduled"
    DEMO_COMPLETED = "demo_completed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (SHORTLISTED, "Shortlisted"),
        (DEMO_REQUESTED, "Demo requested"),
        (DEMO_SCHEDULED, "Demo scheduled"),
        (DEMO_COMPLETED, "Demo completed"),
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
    ]

    post = models.ForeignKey(TuitionPost, on_delete=models.CASCADE, related_name="applications")
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    match_percent = models.PositiveSmallIntegerField(default=80)
    applied_at = models.DateTimeField(auto_now_add=True)
    shortlisted_on = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("post", "tutor")
        ordering = ["-match_percent"]

    def __str__(self):
        return f"{self.tutor} -> {self.post}"

    @property
    def demo_obj(self):
        return DemoClass.objects.filter(application=self).first()

    @property
    def note(self):
        d = self.demo_obj
        if self.status == self.PENDING:
            return "Applied recently"
        if self.status == self.SHORTLISTED:
            when = self.shortlisted_on.strftime("%b %d") if self.shortlisted_on else "earlier"
            return f"Shortlisted by you on {when}"
        if self.status == self.DEMO_REQUESTED:
            return "Demo requested · waiting for the tutor to confirm a time"
        if self.status == self.DEMO_SCHEDULED and d:
            return f"Demo · {d.date:%a %d %b}, {d.time:%I:%M %p} ({d.get_platform_display()})"
        if self.status == self.DEMO_COMPLETED:
            return "Demo completed · awaiting your decision"
        if self.status == self.ACCEPTED:
            return "Accepted · tuition can start"
        return "Rejected"

    # ---- actions from the class diagram: accept(), reject(), cancel() ----
    def shortlist(self):
        if self.status != self.PENDING:
            return False
        self.status = self.SHORTLISTED
        self.shortlisted_on = date.today()
        self.save()
        return True

    def request_demo(self):
        """One demo per tutor-post pair (OneToOne)."""
        if self.status != self.SHORTLISTED:
            return False
        demo, created = DemoClass.objects.get_or_create(
            application=self,
            defaults={
                "subject": self.post.subject,
                "date": date.today() + timedelta(days=1),
                "time": time(17, 0),
            },
        )
        if not created:
            demo.status = DemoClass.REQUESTED
            demo.save()
        self.status = self.DEMO_REQUESTED
        self.save()
        return True

    def cancel(self):
        d = self.demo_obj
        if self.status not in (self.DEMO_REQUESTED, self.DEMO_SCHEDULED) or not d:
            return False
        d.status = DemoClass.CANCELLED
        d.save()
        self.status = self.SHORTLISTED
        self.save()
        return True

    def accept(self):
        d = self.demo_obj
        if self.status != self.DEMO_COMPLETED or not d:
            return False
        d.status = DemoClass.ACCEPTED
        d.save()
        self.status = self.ACCEPTED
        self.save()
        return True

    def reject(self):
        if self.status in (self.ACCEPTED, self.REJECTED):
            return False
        d = self.demo_obj
        if d and d.status in (DemoClass.REQUESTED, DemoClass.SCHEDULED, DemoClass.COMPLETED):
            d.status = DemoClass.REJECTED
            d.save()
        self.status = self.REJECTED
        self.save()
        return True


class DemoClass(models.Model):
    REQUESTED = "requested"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

    STATUS_CHOICES = [
        (REQUESTED, "Requested"),
        (SCHEDULED, "Scheduled"),
        (COMPLETED, "Demo completed"),
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
        (CANCELLED, "Cancelled"),
        (NO_SHOW, "Tutor no-show"),
    ]
    PLATFORM_CHOICES = [("meet", "Google Meet"), ("zoom", "Zoom")]

    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="demo")
    subject = models.CharField(max_length=60)
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=30)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default="meet")
    meeting_link = models.URLField(blank=True, default="https://meet.google.com/tlk-demo-xyz")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=REQUESTED)
    requested_on = models.DateField(default=datetime.date.today)
    scheduled_on = models.DateField(null=True, blank=True)
    completed_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"Demo: {self.application}"

    @property
    def tutor(self):
        return self.application.tutor

    # stage = how many timeline steps are finished
    STAGE = {REQUESTED: 1, SCHEDULED: 2, COMPLETED: 3, ACCEPTED: 5, REJECTED: 4,
             CANCELLED: 1, NO_SHOW: 2}

    def timeline(self):
        stage = self.STAGE.get(self.status, 1)
        fmt = lambda d: d.strftime("%b %d") if d else ""
        steps = [
            ("Demo requested", f"{fmt(self.requested_on)} · by Ayesha"),
            ("Demo scheduled", f"{fmt(self.scheduled_on)} · by {self.tutor.name.split()[0]}" if self.scheduled_on else "Waiting for the tutor"),
            ("Demo completed", f"{fmt(self.completed_on)} · {self.duration_minutes} min" if self.completed_on else "After the class"),
            ("Your decision", "Waiting for you" if stage == 3 else ("Done" if stage > 3 else "After the demo")),
            ("Tuition starts", "After acceptance"),
        ]
        out = []
        for i, (label, sub) in enumerate(steps):
            state = "done" if i < stage else ("current" if i == stage else "todo")
            out.append({"label": label, "sub": sub, "state": state})
        return out

    # ---- class diagram: schedule_demo(), confirm_tutor() ----
    def schedule_demo(self, new_date, new_time):
        self.date, self.time = new_date, new_time
        self.status = self.SCHEDULED
        self.scheduled_on = date.today()
        self.save()
        self.application.status = Application.DEMO_SCHEDULED
        self.application.save()
