from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from reviews.models import Review


class ReviewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='ayesha_rahman',
            email='ayesha.rahman@gmail.com',
            password='password123',
            first_name='Ayesha',
            last_name='Rahman'
        )
        self.tutor = User.objects.create_user(
            username='tanvir_hasan',
            email='tanvir.hasan@buet.ac.bd',
            password='password123',
            first_name='Tanvir',
            last_name='Hasan'
        )

    def test_rate_tutor_get(self):
        """Test GET request to rate tutor page loads successfully."""
        response = self.client.get(reverse('reviews:rate_tutor'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tanvir Hasan')
        self.assertContains(response, 'Overall rating')

    def test_submit_review_post(self):
        """Test submitting a review form creates a Review object."""
        post_data = {
            'overall_rating': 5,
            'subject_knowledge': 5,
            'communication': 5,
            'punctuality': 4,
            'safety_and_respect': 5,
            'review_text': 'Great tutor, very clear explanations.',
            'post_as_verified': True,
        }
        response = self.client.post(reverse('reviews:rate_tutor'), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify saved in DB
        review = Review.objects.filter(reviewee=self.tutor).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.overall_rating, 5)
        self.assertEqual(review.subject_knowledge, 5)
        self.assertTrue(review.post_as_verified)

    def test_review_history_page(self):
        """Test review history page renders existing reviews."""
        Review.objects.create(
            reviewer=self.student,
            reviewee=self.tutor,
            tuition_title='Tuition: Mathematics · Class 10',
            overall_rating=5,
            subject_knowledge=5,
            communication=5,
            punctuality=5,
            safety_and_respect=5,
            review_text='Excellent performance.'
        )
        response = self.client.get(reverse('reviews:review_history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Excellent performance.')
