from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from reviews.models import Review
from notifications.models import Notification, NotificationType


class Command(BaseCommand):
    help = 'Seed initial demo data for TutorLink Rate & Review and Notifications'

    def handle(self, *args, **options):
        self.stdout.write("Seeding TutorLink data...")

        # 1. Create or get users
        ayesha, _ = User.objects.get_or_create(
            username='ayesha_rahman',
            defaults={
                'first_name': 'Ayesha',
                'last_name': 'Rahman',
                'email': 'ayesha.rahman@gmail.com'
            }
        )
        if not ayesha.has_usable_password():
            ayesha.set_password('student123')
            ayesha.save()

        tanvir, _ = User.objects.get_or_create(
            username='tanvir_hasan',
            defaults={
                'first_name': 'Tanvir',
                'last_name': 'Hasan',
                'email': 'tanvir.hasan@buet.ac.bd'
            }
        )
        if not tanvir.has_usable_password():
            tanvir.set_password('tutor123')
            tanvir.save()

        nusrat, _ = User.objects.get_or_create(
            username='nusrat_jahan',
            defaults={
                'first_name': 'Nusrat',
                'last_name': 'Jahan',
                'email': 'nusrat.jahan@du.ac.bd'
            }
        )

        imran, _ = User.objects.get_or_create(
            username='imran_hossain',
            defaults={
                'first_name': 'Imran',
                'last_name': 'Hossain',
                'email': 'imran.hossain@du.ac.bd'
            }
        )

        # 2. Seed Reviews for Tanvir (to match 48 reviews, 4.9 score, breakdown: 88% 5-star, 10% 4-star, 2% 3-star)
        if Review.objects.filter(reviewee=tanvir).count() < 48:
            Review.objects.filter(reviewee=tanvir).delete()
            # 42 reviews of 5-star (87.5% -> 88%)
            # 5 reviews of 4-star (10.4% -> 10%)
            # 1 review of 3-star (2.1% -> 2%)
            # Total = 48 reviews.
            reviews_to_create = []

            # First, featured review from Ayesha:
            reviews_to_create.append(Review(
                reviewer=ayesha,
                reviewee=tanvir,
                tuition_title='Tuition: Mathematics · Class 10 · Sep–Oct 2026',
                review_type=Review.ReviewType.STUDENT_TO_TUTOR,
                overall_rating=5,
                subject_knowledge=5,
                communication=5,
                punctuality=5,
                safety_and_respect=5,
                review_text='Explained every step clearly and always shared weekly progress with my parents. The online demo made us comfortable before we started.',
                post_as_verified=True
            ))

            # Other 5-star reviews:
            for i in range(41):
                reviews_to_create.append(Review(
                    reviewer=ayesha,
                    reviewee=tanvir,
                    tuition_title='Tuition: Mathematics · Class 10',
                    review_type=Review.ReviewType.STUDENT_TO_TUTOR,
                    overall_rating=5,
                    subject_knowledge=5,
                    communication=5,
                    punctuality=4 if i % 2 == 0 else 5,
                    safety_and_respect=5,
                    review_text=f'Great learning experience with Tanvir sir. Session #{i+2}',
                    post_as_verified=True
                ))

            # 4-star reviews:
            for i in range(5):
                reviews_to_create.append(Review(
                    reviewer=ayesha,
                    reviewee=tanvir,
                    tuition_title='Tuition: Mathematics · Class 9',
                    review_type=Review.ReviewType.STUDENT_TO_TUTOR,
                    overall_rating=4,
                    subject_knowledge=5,
                    communication=4,
                    punctuality=4,
                    safety_and_respect=5,
                    review_text='Good tutor, helped improve exam problem solving skills.',
                    post_as_verified=True
                ))

            # 3-star review:
            reviews_to_create.append(Review(
                reviewer=ayesha,
                reviewee=tanvir,
                tuition_title='Tuition: Physics · Class 10',
                review_type=Review.ReviewType.STUDENT_TO_TUTOR,
                overall_rating=3,
                subject_knowledge=4,
                communication=3,
                punctuality=3,
                safety_and_respect=4,
                review_text='Satisfactory explanation of topics.',
                post_as_verified=False
            ))

            Review.objects.bulk_create(reviews_to_create)
            self.stdout.write(self.style.SUCCESS(f"Created {len(reviews_to_create)} reviews for Tanvir Hasan."))

        # 3. Seed Notifications matching Slide 17 exactly:
        if Notification.objects.filter(recipient=ayesha).count() < 7:
            Notification.objects.filter(recipient=ayesha).delete()
            now = timezone.now()
            
            sample_notifications = [
                # 1. Match (unread)
                Notification(
                    recipient=ayesha,
                    notification_type=NotificationType.MATCH,
                    title="New 95% match found",
                    description="Tanvir Hasan matches your Math · Class 10 post.",
                    is_read=False,
                    created_at=now - timedelta(minutes=5)
                ),
                # 2. Application (unread)
                Notification(
                    recipient=ayesha,
                    notification_type=NotificationType.APPLICATION,
                    title="Nusrat Jahan applied to your post",
                    description="Review her profile and shortlist.",
                    is_read=False,
                    created_at=now - timedelta(minutes=40)
                ),
                # 3. Demo (unread)
                Notification(
                    recipient=ayesha,
                    notification_type=NotificationType.DEMO,
                    title="Demo scheduled for Sat, 5:00 PM",
                    description="Tanvir Hasan sent the meeting link.",
                    is_read=False,
                    created_at=now - timedelta(hours=2)
                ),
                # 4. Verification (read)
                Notification(
                    recipient=ayesha,
                    notification_type=NotificationType.VERIFICATION,
                    title="Your documents were approved",
                    description="Contact & demo features are now unlocked.",
                    is_read=True,
                    created_at=now - timedelta(days=1)
                ),
                # 5. Location (read)
                Notification(
                    recipient=ayesha,
                    notification_type=NotificationType.LOCATION,
                    title="Live location session ended",
                    description="Session with Tanvir Hasan expired automatically.",
                    is_read=True,
                    created_at=now - timedelta(days=1, hours=2)
                ),
                # 6. Review (read)
                Notification(
                    recipient=ayesha,
                    notification_type=NotificationType.REVIEW,
                    title="Rate your completed demo",
                    description="Share feedback about Imran Hossain.",
                    is_read=True,
                    created_at=now - timedelta(days=3)
                ),
                # 7. System (read)
                Notification(
                    recipient=ayesha,
                    notification_type=NotificationType.SYSTEM,
                    title="Welcome to TutorLink",
                    description="Complete your profile for better matches.",
                    is_read=True,
                    created_at=now - timedelta(days=5)
                ),
            ]
            Notification.objects.bulk_create(sample_notifications)
            self.stdout.write(self.style.SUCCESS(f"Created {len(sample_notifications)} notifications matching slide 17."))

        self.stdout.write(self.style.SUCCESS("All seed data created successfully!"))
