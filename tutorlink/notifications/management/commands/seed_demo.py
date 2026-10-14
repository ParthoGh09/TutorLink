from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.models import Notification, NotificationType
from reviews.models import Review, Tuition

User = get_user_model()
PASSWORD = "tutorlink123"


def make_user(username, first, last, role, **extra):
    user, created = User.objects.get_or_create(
        username=username,
        defaults=dict(first_name=first, last_name=last, role=role, email=f"{username}@example.com", **extra),
    )
    if created:
        user.set_password(PASSWORD)
        user.save()
    return user


class Command(BaseCommand):
    help = "Create demo users, notifications, tuitions and reviews."

    def handle(self, *args, **options):
        now = timezone.now()
        make_user("admin", "Iffat Ara", "Mahira", "ADMIN", is_staff=True, is_superuser=True, is_verified=True)
        ayesha = make_user("ayesha", "Ayesha", "Rahman", "STUDENT", area="Dhanmondi, Dhaka", is_verified=True)
        tanvir = make_user("tanvir", "Tanvir", "Hasan", "TUTOR", area="Dhanmondi, Dhaka", is_verified=True)
        nusrat = make_user("nusrat", "Nusrat", "Jahan", "TUTOR", area="Shankar, Dhanmondi", is_verified=True)

        Notification.objects.filter(user=ayesha).delete()
        rows = [
            (NotificationType.MATCH, "New 95% match found", "Tanvir Hasan matches your Math · Class 10 post.", timedelta(minutes=5), False),
            (NotificationType.APPLICATION, "Nusrat Jahan applied to your post", "Review her profile and shortlist.", timedelta(minutes=40), False),
            (NotificationType.DEMO, "Demo scheduled for Sat, 5:00 PM", "Tanvir Hasan sent the meeting link.", timedelta(hours=2), False),
            (NotificationType.VERIFICATION, "Your documents were approved", "Contact & demo features are now unlocked.", timedelta(days=1), True),
            (NotificationType.LOCATION, "Live location session ended", "Session with Tanvir Hasan expired automatically.", timedelta(days=1, hours=1), True),
            (NotificationType.REVIEW, "Rate your completed demo", "Share feedback about Imran Hossain.", timedelta(days=3), True),
            (NotificationType.SYSTEM, "Welcome to TutorLink", "Complete your profile for better matches.", timedelta(days=9), True),
        ]
        for ntype, title, msg, ago, read in rows:
            Notification.objects.create(
                user=ayesha, type=ntype, title=title, message=msg, is_read=read,
                created_at=now - ago,
                link="/reviews/" if ntype == NotificationType.REVIEW else "",
            )

        Tuition.objects.all().delete()
        Tuition.objects.create(student=ayesha, tutor=tanvir, subject="Mathematics", class_level="Class 10",
                               started_on=now.date() - timedelta(days=30), ended_on=now.date(),
                               status=Tuition.Status.CONFIRMED)
        Tuition.objects.create(student=ayesha, tutor=nusrat, subject="Physics", class_level="Class 10",
                               started_on=now.date() - timedelta(days=60), status=Tuition.Status.CONFIRMED)

        scores = [5, 5, 5, 5, 5, 5, 5, 5, 4, 3]
        for i, score in enumerate(scores):
            student = make_user(f"student{i + 1}", f"Student{i + 1}", "Demo", "STUDENT", is_verified=True)
            t = Tuition.objects.create(student=student, tutor=tanvir, subject="Mathematics",
                                       class_level="Class 9", status=Tuition.Status.CONFIRMED)
            Review.objects.create(
                tuition=t, reviewer=student, reviewee=tanvir, overall_rating=score,
                subject_knowledge=score, communication=score, punctuality=score, safety_respect=score,
                comment="Explained every step clearly.", is_verified_post=True,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded. Log in as 'ayesha' or 'tanvir' with password: {PASSWORD}"
        ))