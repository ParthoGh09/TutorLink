from django.contrib.auth.decorators import login_required
from django.db.models import Q
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

    q = request.GET.get('q', '').strip()
    subject = request.GET.get('subject', '')
    class_level = request.GET.get('class_level', '')
    area = request.GET.get('area', '').strip()
    max_budget = request.GET.get('max_budget', '').strip()
    mode = request.GET.get('mode', '')
    min_rating = request.GET.get('min_rating', '')

    if q:
        tutors = tutors.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(user__username__icontains=q)
        )
    if subject.isdigit():
        tutors = tutors.filter(subjects__id=subject)
    if class_level.isdigit():
        tutors = tutors.filter(class_from__lte=int(class_level), class_to__gte=int(class_level))
    if area:
        tutors = tutors.filter(user__area__icontains=area)
    if max_budget.isdigit():
        tutors = tutors.filter(expected_salary__lte=max_budget)
    if mode in ('ONLINE', 'OFFLINE'):
        tutors = tutors.filter(Q(mode=mode) | Q(mode=TutorProfile.Mode.BOTH))
    try:
        if min_rating:
            tutors = tutors.filter(rating__gte=float(min_rating))
    except ValueError:
        pass

    tutors = tutors.distinct().order_by('-rating', '-review_count')

    return render(request, 'tutors/finde_tutors.html', {
        'tutors': tutors,
        'subjects': Subject.objects.all().order_by('name'),
        'class_levels': range(1, 13),
        'filters': request.GET,
    })