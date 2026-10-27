from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Review
from .forms import ReviewForm


def get_or_create_default_users():

    student, _ = User.objects.get_or_create(
        username='ayesha_rahman',
        defaults={'first_name': 'Ayesha', 'last_name': 'Rahman', 'email': 'ayesha.rahman@gmail.com'}
    )
    tutor, _ = User.objects.get_or_create(
        username='tanvir_hasan',
        defaults={'first_name': 'Tanvir', 'last_name': 'Hasan', 'email': 'tanvir.hasan@buet.ac.bd'}
    )
    return student, tutor


def rate_tutor_view(request, tutor_id=None):
    student, default_tutor = get_or_create_default_users()
    
    if tutor_id:
        tutor = get_object_or_404(User, id=tutor_id)
    else:
        tutor = default_tutor

    tuition_title = "Tuition: Mathematics · Class 10 · Sep–Oct 2026"
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user if request.user.is_authenticated else student
            review.reviewee = tutor
            review.tuition_title = tuition_title
            review.review_type = Review.ReviewType.STUDENT_TO_TUTOR
            review.save()
            messages.success(request, f"Your review for {tutor.get_full_name() or tutor.username} has been submitted successfully!")
            return redirect('reviews:rate_tutor')
        else:
            messages.error(request, "Please check the form and fill in all required ratings.")
    else:
        initial_data = {
            'overall_rating': 5,
            'subject_knowledge': 5,
            'communication': 5,
            'punctuality': 4,
            'safety_and_respect': 5,
            'review_text': "Explained every step clearly and always shared weekly progress with my parents. The online demo made us comfortable before we started.",
            'post_as_verified': True
        }
        form = ReviewForm(initial=initial_data)

    rating_summary = Review.get_user_rating_summary(tutor)
    
    context = {
        'form': form,
        'tutor': tutor,
        'tuition_title': tuition_title,
        'rating_summary': rating_summary,
        'current_user': student,
    }
    return render(request, 'reviews/rate_review.html', context)


def review_history_view(request):
    reviews = Review.objects.all().select_related('reviewer', 'reviewee')
    return render(request, 'reviews/review_history.html', {'reviews': reviews})
