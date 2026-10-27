from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import User
from tuitions.forms import TuitionPostForm
from tuitions.models import TuitionPost, TuitionApplication
from .models import Subject, TutorProfile


@login_required
def find_tutors(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("role_dashboard")

    for tutor_user in User.objects.filter(
        role=User.Role.TUTOR
    ).iterator():
        TutorProfile.objects.get_or_create(user=tutor_user)

    tutors = TutorProfile.objects.filter(
        user__role=User.Role.TUTOR
    ).select_related("user").prefetch_related("subjects")

    subject = request.GET.get("subject", "").strip()
    class_level = "".join(
        ch for ch in request.GET.get("class_level", "")
        if ch.isdigit()
    )
    area = request.GET.get("area", "").strip()
    max_budget = request.GET.get("max_budget", "").strip()

    if subject:
        tutors = tutors.filter(subjects__name__icontains=subject)

    if class_level:
        tutors = tutors.filter(
            class_from__lte=int(class_level),
            class_to__gte=int(class_level),
        )

    if area:
        tutors = tutors.filter(user__area__icontains=area)

    if max_budget.isdigit():
        tutors = tutors.filter(
            expected_salary__gt=0,
            expected_salary__lte=int(max_budget),
        )

    tutors = list(tutors.distinct().order_by("-rating", "-review_count"))

    avg_rating = None
    if tutors:
        avg_rating = round(
            sum(float(tutor.rating) for tutor in tutors) / len(tutors),
            1,
        )

    return render(request, "tutors/find_tutors.html", {
        "tutors": tutors,
        "subjects": Subject.objects.all().order_by("name"),
        "class_levels": range(1, 13),
        "filters": request.GET,
        "avg_rating": avg_rating,
        "role_name": "Student",
    })


@login_required
def tutor_detail(request, profile_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    tutor = get_object_or_404(
        TutorProfile.objects.select_related("user").prefetch_related("subjects"),
        pk=profile_id,
        user__role=User.Role.TUTOR,
    )

    return render(request, "tutors/tutor_detail.html", {
        "tutor": tutor,
        "role_name": "Student",
    })


@login_required
def request_tutor(request, profile_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    tutor = get_object_or_404(
        TutorProfile.objects.select_related("user"),
        pk=profile_id,
        user__role=User.Role.TUTOR,
    )

    form = TuitionPostForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST" and form.is_valid():
        tuition = form.save(commit=False)
        tuition.student = request.user
        tuition.target_tutor = tutor.user
        tuition.status = "OPEN"
        tuition.save()

        # Create the tutor's application automatically.
        TuitionApplication.objects.create(
            tuition=tuition,
            tutor=tutor.user,
            status=TuitionApplication.Status.PENDING,
        )

        messages.success(
            request,
            "Your request has been sent to the selected tutor.",
        )
        return redirect("tuitions:applications")

    return render(request, "tuitions/post_form.html", {
        "form": form,
        "title": "Request a Specific Tutor",
        "role_name": "Student",
        "target_tutor": tutor,
    })