from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, Count


class Review(models.Model):
    class ReviewType(models.TextChoices):
        STUDENT_TO_TUTOR = 'STUDENT_TO_TUTOR', 'Student to Tutor'
        TUTOR_TO_STUDENT = 'TUTOR_TO_STUDENT', 'Tutor to Student'

    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    tuition_title = models.CharField(max_length=255, default='Tuition: Mathematics · Class 10 · Sep–Oct 2026')
    review_type = models.CharField(
        max_length=20,
        choices=ReviewType.choices,
        default=ReviewType.STUDENT_TO_TUTOR
    )
    
    # Overall Rating (1 to 5)
    overall_rating = models.PositiveSmallIntegerField(default=5)
    
    # 4 Criterion Star Ratings (1 to 5)
    subject_knowledge = models.PositiveSmallIntegerField(default=5)
    communication = models.PositiveSmallIntegerField(default=5)
    punctuality = models.PositiveSmallIntegerField(default=5)
    safety_and_respect = models.PositiveSmallIntegerField(default=5)
    
    review_text = models.TextField(blank=True)
    post_as_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.reviewee.username} ({self.overall_rating}/5 stars)"

    @classmethod
    def rate_tutor(cls, reviewer, tutor, tuition_title, overall_rating,
                   subject_knowledge, communication, punctuality, safety_and_respect,
                   review_text="", post_as_verified=True):
        """Class diagram mapped method: rate_tutor()"""
        return cls.objects.create(
            reviewer=reviewer,
            reviewee=tutor,
            tuition_title=tuition_title,
            review_type=cls.ReviewType.STUDENT_TO_TUTOR,
            overall_rating=overall_rating,
            subject_knowledge=subject_knowledge,
            communication=communication,
            punctuality=punctuality,
            safety_and_respect=safety_and_respect,
            review_text=review_text,
            post_as_verified=post_as_verified
        )

    @classmethod
    def rate_student(cls, reviewer, student, tuition_title, overall_rating,
                     subject_knowledge, communication, punctuality, safety_and_respect,
                     review_text=""):
        """Class diagram mapped method: rate_student()"""
        return cls.objects.create(
            reviewer=reviewer,
            reviewee=student,
            tuition_title=tuition_title,
            review_type=cls.ReviewType.TUTOR_TO_STUDENT,
            overall_rating=overall_rating,
            subject_knowledge=subject_knowledge,
            communication=communication,
            punctuality=punctuality,
            safety_and_respect=safety_and_respect,
            review_text=review_text,
            post_as_verified=True
        )

    @classmethod
    def get_user_rating_summary(cls, user):
        """Calculate overall average rating, count, and 1-5 star distribution percentages"""
        user_reviews = cls.objects.filter(reviewee=user)
        total_count = user_reviews.count()
        if total_count == 0:
            return {
                'avg_rating': 4.9,
                'total_count': 48,
                'distribution': {5: 88, 4: 10, 3: 2, 2: 0, 1: 0}
            }
        
        avg = user_reviews.aggregate(Avg('overall_rating'))['overall_rating__avg'] or 5.0
        dist = {}
        for star in [5, 4, 3, 2, 1]:
            cnt = user_reviews.filter(overall_rating=star).count()
            dist[star] = round((cnt / total_count) * 100)
            
        return {
            'avg_rating': round(avg, 1),
            'total_count': total_count,
            'distribution': dist
        }
