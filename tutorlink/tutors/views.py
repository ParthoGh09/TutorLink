from datetime import date, time as dtime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from .models import DemoClass, Subject, TutorProfile

# Demo time choices: 4:00 PM to 9:00 PM, as (value, label)
TIME_SLOTS = [
    (f'{h:02d}:00', f'{h % 12 or 12}:00 {"AM" if h < 12 else "PM"}')
    for h in range(16, 22)
]


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

    return render(request, 'tutors/find_tutors.html', {
        'tutors': tutors,
        'subjects': Subject.objects.all().order_by('name'),
        'class_levels': range(1, 13),
        'filters': request.GET,
    })

@login_required
def tutor_profile(request, pk):
    if request.user.role != User.Role.STUDENT:
        return redirect('role_dashboard')

    tutor = get_object_or_404(
        TutorProfile.objects.select_related('user').prefetch_related('subjects'),
        pk=pk, user__is_verified=True,
    )
    existing_demo = DemoClass.objects.filter(student=request.user, tutor=tutor).first()

    if request.method == 'POST':
        if existing_demo:
            messages.warning(request, 'You have already requested a demo with this tutor.')
            return redirect('tutor_profile', pk=tutor.pk)

        subject_id = request.POST.get('subject', '')
        time_text = request.POST.get('time', '')
        platform = request.POST.get('platform', '')

        try:
            demo_date = date.fromisoformat(request.POST.get('date', ''))
        except ValueError:
            demo_date = None

        subject = tutor.subjects.filter(pk=subject_id).first() if subject_id.isdigit() else None

        if demo_date is None or demo_date < timezone.localdate():
            messages.error(request, 'Please choose a valid date (today or later).')
        elif time_text not in [value for value, label in TIME_SLOTS]:
            messages.error(request, 'Please choose a valid time.')
        elif platform not in DemoClass.Platform.values:
            messages.error(request, 'Please choose Google Meet or Zoom.')
        elif subject_id and subject is None:
            messages.error(request, "Please choose one of this tutor's subjects.")
        else:
            try:
                DemoClass.objects.create(
                    student=request.user,
                    tutor=tutor,
                    subject=subject,
                    date=demo_date,
                    time=dtime.fromisoformat(time_text),
                    platform=platform,
                )
                messages.success(request, 'Demo class requested! The tutor will confirm the time.')
            except IntegrityError:
                messages.warning(request, 'You have already requested a demo with this tutor.')

        return redirect('tutor_profile', pk=tutor.pk)

    return render(request, 'tutors/tutor_profile.html', {
        'tutor': tutor,
        'existing_demo': existing_demo,
        'time_slots': TIME_SLOTS,
        'today': timezone.localdate(),
    })