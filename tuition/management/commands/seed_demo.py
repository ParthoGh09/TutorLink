from datetime import date, time, timedelta

from django.core.management.base import BaseCommand

from tuition.models import Application, DemoClass, TuitionPost, Tutor


class Command(BaseCommand):
    help = "Fill the database with sample data that matches the UI design PDF."

    def handle(self, *args, **options):
        DemoClass.objects.all().delete()
        Application.objects.all().delete()
        TuitionPost.objects.all().delete()
        Tutor.objects.all().delete()

        today = date.today()
        post = TuitionPost.objects.create(subject="Mathematics", class_level="Class 10")

        tanvir = Tutor.objects.create(name="Tanvir Hasan", institution="EEE · BUET", rating="4.9",
                                      expected_fee=6500, area="Dhanmondi, Dhaka", avatar_color="#DCE3FF")
        nusrat = Tutor.objects.create(name="Nusrat Jahan", institution="Physics · University of Dhaka", rating="4.8",
                                      expected_fee=6000, area="Shankar, Dhanmondi", avatar_color="#D5F2E6")
        imran = Tutor.objects.create(name="Imran Hossain", institution="Mathematics · University of Dhaka", rating="4.6",
                                     expected_fee=5500, area="Kalabagan, Dhaka", avatar_color="#FFDCD6")
        farzana = Tutor.objects.create(name="Farzana Islam", institution="English · North South University", rating="4.7",
                                       expected_fee=5000, area="Mirpur Road, Dhaka", avatar_color="#FBE77B")

        a1 = Application.objects.create(post=post, tutor=tanvir, status=Application.DEMO_COMPLETED, match_percent=95)
        a2 = Application.objects.create(post=post, tutor=nusrat, status=Application.DEMO_SCHEDULED, match_percent=89)
        Application.objects.create(post=post, tutor=imran, status=Application.SHORTLISTED, match_percent=83,
                                   shortlisted_on=today - timedelta(days=1))
        Application.objects.create(post=post, tutor=farzana, status=Application.PENDING, match_percent=72)

        DemoClass.objects.create(application=a1, subject="Mathematics", date=today - timedelta(days=1),
                                 time=time(17, 0), platform="meet", status=DemoClass.COMPLETED,
                                 requested_on=today - timedelta(days=4), scheduled_on=today - timedelta(days=3),
                                 completed_on=today - timedelta(days=1))
        DemoClass.objects.create(application=a2, subject="Physics", date=today + timedelta(days=1),
                                 time=time(18, 0), platform="zoom", status=DemoClass.SCHEDULED,
                                 meeting_link="https://zoom.us/j/1234567890",
                                 requested_on=today - timedelta(days=2), scheduled_on=today - timedelta(days=1))

        self.stdout.write(self.style.SUCCESS("Sample data created. Now run: python manage.py runserver"))
