from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import User
from .models import Subject, TutorProfile


@login_required
def find_tutors(request):
    if request.user.role != User.Role.STUDENT:
        return redirect('role_dashboard')

    tutors = (
        TutorProfile.objects.filter(user__is_verified=True)
        .select_related('user')
        .prefetch_related('subjects')
    )

    subject = request.GET.get('subject', '').strip()
    class_level = ''.join(ch for ch in request.GET.get('class_level', '') if ch.isdigit())
    area = request.GET.get('area', '').strip()
    max_budget = request.GET.get('max_budget', '').strip()

    if subject:
        tutors = tutors.filter(subjects__name__icontains=subject)
    if class_level.isdigit():
        tutors = tutors.filter(class_from__lte=int(class_level), class_to__gte=int(class_level))
    if area:
        tutors = tutors.filter(user__area__icontains=area)
    if max_budget.isdigit():
        tutors = tutors.filter(expected_salary__lte=max_budget)

    tutors = list(tutors.distinct().order_by('-rating', '-review_count'))

    avg_rating = None
    if tutors:
        avg_rating = round(sum(float(t.rating) for t in tutors) / len(tutors), 1)

    return render(request, 'tutors/find_tutors.html', {
        'tutors': tutors,
        'subjects': Subject.objects.all().order_by('name'),
        'class_levels': range(1, 13),
        'filters': request.GET,
        'avg_rating': avg_rating,
        'role_name': 'Student',
    })