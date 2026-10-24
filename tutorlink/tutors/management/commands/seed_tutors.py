from django.core.management.base import BaseCommand

from accounts.models import User
from tutors.models import Subject, TutorProfile

# username, first, last, university, department, area, subjects,
# class_from, class_to, salary, mode, experience, time,
TUTORS = [
    ('tanvir', 'Tanvir', 'Hasan', 'BUET', 'EEE', 'Dhanmondi',
     ['Math', 'Physics'], 9, 12, 6500, 'BOTH', 3, 'Sat-Thu, 4-9 PM'),
    ('imran', 'Imran', 'Hossain', 'University of Dhaka', 'Mathematics', 'Kalabagan',
     ['Math', 'Higher Math'], 6, 10, 5500, 'BOTH', 2, 'Sat-Thu, 4-9 PM'),
    ('farzana', 'Farzana', 'Islam', 'North South University', 'English', 'Mirpur Road',
     ['English', 'ICT'], 6, 9, 5000, 'ONLINE', 1, 'Sat-Thu, 4-9 PM'),
]


class Command(BaseCommand):
    help = 'Create sample tutors for testing (password: test12345)'

    def handle(self, *args, **options):
        for (username, first, last, uni, dept, area, subjects, c_from, c_to,
             salary, mode, exp, time) in TUTORS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults=dict(
                    email=f'{username}@example.com', first_name=first, last_name=last,
                    role=User.Role.TUTOR, division='Dhaka', district='Dhaka',
                    area=area, is_verified=True,
                ),
            )
            if created:
                user.set_password('test12345')
                user.save()

            profile, _ = TutorProfile.objects.get_or_create(
                user=user,
                defaults=dict(
                    university=uni, department=dept, class_from=c_from, class_to=c_to,
                    expected_salary=salary, mode=mode, experience_years=exp,
                    available_time=time,
                ),
            )
            profile.subjects.set([Subject.objects.get_or_create(name=s)[0] for s in subjects])

        self.stdout.write(self.style.SUCCESS('Sample tutors ready.'))