from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from tutors.models import DemoClass, Subject, TutorProfile
from .forms import TuitionPostForm, DemoScheduleForm, TuitionReviewForm
from .models import TuitionPost, TuitionApplication


def is_admin(user):
    return user.is_superuser or str(
        getattr(user, "role", "")
    ).upper() == "ADMIN"


def is_student(user):
    return str(getattr(user, "role", "")).upper() == "STUDENT"


def is_tutor(user):
    return str(getattr(user, "role", "")).upper() == "TUTOR"


def _demo_for_application(application):
    return DemoClass.objects.filter(
        student_id=application.tuition.student_id,
        tutor__user_id=application.tutor_id,
    ).select_related("tutor", "subject").first()


@login_required
def post_list(request):
    my_applications = set()
    applications_by_tuition = {}

    if is_tutor(request.user):
        posts = TuitionPost.objects.filter(
            status="OPEN"
        ).filter(
            Q(target_tutor__isnull=True)
            | Q(target_tutor=request.user)
        ).select_related(
            "student", "target_tutor"
        ).order_by("-created_at")

        tutor_applications = TuitionApplication.objects.filter(
            tutor=request.user
        ).select_related("tuition")

        for application in tutor_applications:
            my_applications.add(application.tuition_id)
            applications_by_tuition[application.tuition_id] = application

        subject = request.GET.get("subject", "").strip()
        class_level = request.GET.get("class_level", "").strip()
        area = request.GET.get("area", "").strip()
        min_budget = request.GET.get("min_budget", "").strip()
        max_budget = request.GET.get("max_budget", "").strip()
        mode = request.GET.get("mode", "").strip()

        if subject:
            posts = posts.filter(subject__icontains=subject)

        if class_level:
            posts = posts.filter(class_level__icontains=class_level)

        if area:
            posts = posts.filter(
                Q(area__icontains=area)
                | Q(district__icontains=area)
                | Q(division__icontains=area)
            )

        if min_budget.isdigit():
            posts = posts.filter(budget_max__gte=int(min_budget))

        if max_budget.isdigit():
            posts = posts.filter(budget_min__lte=int(max_budget))

        if mode in ("ONLINE", "OFFLINE"):
            posts = posts.filter(teaching_mode=mode)

        # Attach the tutor's complete application to each post.
        for post in posts:
            post.my_application = applications_by_tuition.get(post.pk)

    elif is_student(request.user):
        posts = TuitionPost.objects.filter(
            student=request.user
        ).select_related(
            "student", "target_tutor"
        ).order_by("-created_at")

    elif is_admin(request.user):
        posts = TuitionPost.objects.select_related(
            "student", "target_tutor"
        ).order_by("-created_at")

    else:
        raise PermissionDenied

    return render(request, "tuitions/post_list.html", {
        "posts": posts,
        "my_applications": my_applications,
        "is_student": is_student(request.user),
        "is_tutor": is_tutor(request.user),
        "is_admin": is_admin(request.user),
        "role_name": request.user.get_role_display(),
        "filters": request.GET,
    })


@login_required
def post_detail(request, pk):
    post = get_object_or_404(
        TuitionPost.objects.select_related(
            "student", "target_tutor"
        ),
        pk=pk,
    )

    can_manage = (
        post.student_id == request.user.pk
        or is_admin(request.user)
    )
    my_application = None

    if is_tutor(request.user):
        if (
            post.target_tutor_id is not None
            and post.target_tutor_id != request.user.pk
        ):
            raise PermissionDenied

        my_application = TuitionApplication.objects.filter(
            tuition=post,
            tutor=request.user,
        ).first()

        if post.status != "OPEN" and my_application is None:
            raise PermissionDenied

    elif not can_manage:
        raise PermissionDenied

    applications_qs = (
        post.applications.select_related("tutor")
        if can_manage else []
    )

    return render(request, "tuitions/post_detail.html", {
        "post": post,
        "my_application": my_application,
        "applications": applications_qs,
        "can_manage": can_manage,
        "can_apply": (
            is_tutor(request.user)
            and post.status == "OPEN"
            and my_application is None
            and post.target_tutor_id is None
        ),
        "is_admin": is_admin(request.user),
        "role_name": request.user.get_role_display(),
    })


@login_required
def create_post(request):
    if not (is_student(request.user) or is_admin(request.user)):
        raise PermissionDenied

    form = TuitionPostForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.student = request.user
        post.target_tutor = None
        post.status = "OPEN"
        post.save()

        messages.success(request, "Tuition post created successfully.")
        return redirect("tuitions:post_list")

    return render(request, "tuitions/post_form.html", {
        "form": form,
        "title": "Create Tuition Post",
        "role_name": request.user.get_role_display(),
    })


@login_required
def edit_post(request, pk):
    post = get_object_or_404(TuitionPost, pk=pk)

    if post.student_id != request.user.pk and not is_admin(request.user):
        raise PermissionDenied

    old_image_name = post.image.name if post.image else None

    form = TuitionPostForm(
        request.POST or None,
        request.FILES or None,
        instance=post,
    )

    if request.method == "POST" and form.is_valid():
        updated_post = form.save()
        new_image_name = (
            updated_post.image.name if updated_post.image else None
        )

        if (
            old_image_name
            and old_image_name != new_image_name
            and default_storage.exists(old_image_name)
        ):
            default_storage.delete(old_image_name)

        messages.success(request, "Tuition post updated.")
        return redirect("tuitions:post_list")

    return render(request, "tuitions/post_form.html", {
        "form": form,
        "title": "Edit Tuition Post",
        "role_name": request.user.get_role_display(),
    })


@login_required
@require_POST
def delete_post(request, pk):
    post = get_object_or_404(TuitionPost, pk=pk)

    if post.student_id != request.user.pk and not is_admin(request.user):
        raise PermissionDenied

    if post.image:
        post.image.delete(save=False)

    post.delete()
    messages.success(request, "Tuition post deleted.")
    return redirect("tuitions:post_list")


@login_required
@require_POST
def apply_for_tuition(request, pk):
    if not is_tutor(request.user):
        raise PermissionDenied

    post = get_object_or_404(TuitionPost, pk=pk, status="OPEN")

    if (
        post.target_tutor_id is not None
        and post.target_tutor_id != request.user.pk
    ):
        raise PermissionDenied

    # A personal request already has an application for its selected tutor.
    if post.target_tutor_id == request.user.pk:
        messages.info(
            request,
            "This is a personal request. Review it from My Applications.",
        )
        return redirect("tuitions:applications")

    application = TuitionApplication.objects.filter(
        tuition=post,
        tutor=request.user,
    ).first()

    if application is None:
        TuitionApplication.objects.create(
            tuition=post,
            tutor=request.user,
            status=TuitionApplication.Status.PENDING,
        )
        messages.success(request, "Your application was submitted.")

    elif application.status == TuitionApplication.Status.REJECTED:
        application.status = TuitionApplication.Status.PENDING
        application.review_rating = None
        application.review_text = ""
        application.reviewed_at = None
        application.save(update_fields=[
            "status", "review_rating", "review_text", "reviewed_at"
        ])
        messages.success(request, "Your application was submitted again.")

    else:
        messages.info(request, "You have already applied for this tuition.")

    return redirect("tuitions:applications")


@login_required
def applications(request):
    if is_student(request.user):
        received_applications = TuitionApplication.objects.filter(
            tuition__student=request.user
        ).select_related("tuition", "tutor", "tuition__target_tutor")
        my_applications = None

    elif is_tutor(request.user):
        received_applications = None
        my_applications = TuitionApplication.objects.filter(
            tutor=request.user
        ).select_related("tuition", "tuition__student")

    elif is_admin(request.user):
        received_applications = TuitionApplication.objects.select_related(
            "tuition", "tutor", "tuition__student"
        )
        my_applications = None

    else:
        raise PermissionDenied

    return render(request, "tuitions/applications.html", {
        "received_applications": received_applications,
        "my_applications": my_applications,
        "is_student": is_student(request.user),
        "is_tutor": is_tutor(request.user),
        "is_admin": is_admin(request.user),
        "role_name": request.user.get_role_display(),
    })


@login_required
@require_POST
def accept_application(request, application_id):
    application = get_object_or_404(
        TuitionApplication.objects.select_related(
            "tuition", "tuition__student", "tuition__target_tutor"
        ),
        pk=application_id,
    )
    post = application.tuition

    personal_request = post.target_tutor_id is not None

    if personal_request:
        if not is_tutor(request.user):
            raise PermissionDenied
        if post.target_tutor_id != request.user.pk:
            raise PermissionDenied
        if application.tutor_id != request.user.pk:
            raise PermissionDenied
    else:
        if not (is_student(request.user) or is_admin(request.user)):
            raise PermissionDenied
        if post.student_id != request.user.pk and not is_admin(request.user):
            raise PermissionDenied

    with transaction.atomic():
        post = TuitionPost.objects.select_for_update().get(pk=post.pk)
        application = TuitionApplication.objects.select_for_update().get(
            pk=application.pk
        )

        if (
            post.status != "OPEN"
            or application.status != TuitionApplication.Status.PENDING
        ):
            messages.error(request, "This request is no longer available.")
            if is_tutor(request.user):
                return redirect("tuitions:post_list")
            return redirect("tuitions:applications")

        application.status = TuitionApplication.Status.ACCEPTED
        application.save(update_fields=["status"])

        TuitionApplication.objects.filter(
            tuition=post,
            status=TuitionApplication.Status.PENDING,
        ).exclude(pk=application.pk).update(
            status=TuitionApplication.Status.REJECTED
        )

        post.status = "FILLED"
        post.save(update_fields=["status"])

    messages.success(
        request,
        "Request accepted. The tutor can now schedule the demo class.",
    )

    if is_tutor(request.user):
        return redirect("tuitions:post_list")

    return redirect("tuitions:applications")


@login_required
@require_POST
def reject_application(request, application_id):
    application = get_object_or_404(
        TuitionApplication.objects.select_related(
            "tuition", "tuition__target_tutor"
        ),
        pk=application_id,
    )
    post = application.tuition

    personal_request = post.target_tutor_id is not None

    if personal_request:
        if not is_tutor(request.user):
            raise PermissionDenied
        if post.target_tutor_id != request.user.pk:
            raise PermissionDenied
        if application.tutor_id != request.user.pk:
            raise PermissionDenied
    else:
        if not (is_student(request.user) or is_admin(request.user)):
            raise PermissionDenied
        if post.student_id != request.user.pk and not is_admin(request.user):
            raise PermissionDenied

    if application.status != TuitionApplication.Status.PENDING:
        messages.error(request, "This request has already been processed.")
    else:
        application.status = TuitionApplication.Status.REJECTED
        application.save(update_fields=["status"])

        if personal_request:
            post.status = "CLOSED"
            post.save(update_fields=["status"])

        messages.success(request, "Request rejected.")

    if is_tutor(request.user):
        return redirect("tuitions:post_list")

    return redirect("tuitions:applications")


@login_required
def demo_classes(request):
    if is_student(request.user):
        accepted_applications = TuitionApplication.objects.filter(
            tuition__student=request.user,
            status=TuitionApplication.Status.ACCEPTED,
        ).select_related("tuition", "tutor")

    elif is_tutor(request.user):
        accepted_applications = TuitionApplication.objects.filter(
            tutor=request.user,
            status=TuitionApplication.Status.ACCEPTED,
        ).select_related("tuition", "tuition__student")

    elif is_admin(request.user):
        accepted_applications = TuitionApplication.objects.filter(
            status=TuitionApplication.Status.ACCEPTED,
        ).select_related("tuition", "tuition__student", "tutor")

    else:
        raise PermissionDenied

    demo_items = [
        {
            "application": application,
            "demo": _demo_for_application(application),
        }
        for application in accepted_applications
    ]

    return render(request, "tuitions/demo_classes.html", {
        "demo_items": demo_items,
        "is_student": is_student(request.user),
        "is_tutor": is_tutor(request.user),
        "is_admin": is_admin(request.user),
        "role_name": request.user.get_role_display(),
    })


@login_required
@require_POST
def schedule_demo(request, application_id):
    if not is_tutor(request.user):
        raise PermissionDenied

    application = get_object_or_404(
        TuitionApplication.objects.select_related("tuition"),
        pk=application_id,
        tutor=request.user,
        status=TuitionApplication.Status.ACCEPTED,
    )

    form = DemoScheduleForm(request.POST)
    if not form.is_valid():
        messages.error(
            request,
            "Please provide a valid date, time, platform, and meeting link.",
        )
        return redirect("tuitions:demo_classes")

    tutor_profile = TutorProfile.objects.filter(user=request.user).first()
    if tutor_profile is None:
        messages.error(request, "Your tutor profile was not found.")
        return redirect("tuitions:demo_classes")

    existing_demo = _demo_for_application(application)
    if existing_demo and existing_demo.status == DemoClass.Status.COMPLETED:
        messages.error(request, "This demo has already been completed.")
        return redirect("tuitions:demo_classes")

    subject_obj = Subject.objects.filter(
        name__iexact=str(application.tuition.subject)
    ).first()

    values = {
        "date": form.cleaned_data["date"],
        "time": form.cleaned_data["time"],
        "platform": form.cleaned_data["platform"],
        "meeting_link": form.cleaned_data["meeting_link"],
        "status": DemoClass.Status.SCHEDULED,
        "subject": subject_obj,
    }

    if existing_demo:
        for field, value in values.items():
            setattr(existing_demo, field, value)
        existing_demo.save()
    else:
        DemoClass.objects.create(
            student=application.tuition.student,
            tutor=tutor_profile,
            **values,
        )

    messages.success(request, "Demo scheduled successfully.")
    return redirect("tuitions:demo_detail", application_id=application.pk)


@login_required
def demo_detail(request, application_id):
    application = get_object_or_404(
        TuitionApplication.objects.select_related(
            "tuition", "tuition__student", "tutor"
        ),
        pk=application_id,
        status=TuitionApplication.Status.ACCEPTED,
    )

    allowed = (
        request.user.pk == application.tutor_id
        or request.user.pk == application.tuition.student_id
        or is_admin(request.user)
    )
    if not allowed:
        raise PermissionDenied

    return render(request, "tuitions/demo_detail.html", {
        "application": application,
        "demo": _demo_for_application(application),
        "is_tutor": is_tutor(request.user),
        "is_student": is_student(request.user),
        "is_admin": is_admin(request.user),
        "role_name": request.user.get_role_display(),
    })


@login_required
@require_POST
def complete_demo(request, application_id):
    if not (is_student(request.user) or is_admin(request.user)):
        raise PermissionDenied

    application = get_object_or_404(
        TuitionApplication.objects.select_related("tuition"),
        pk=application_id,
        status=TuitionApplication.Status.ACCEPTED,
    )

    if (
        application.tuition.student_id != request.user.pk
        and not is_admin(request.user)
    ):
        raise PermissionDenied

    demo = _demo_for_application(application)
    if not demo or not demo.meeting_link:
        messages.error(request, "The tutor has not scheduled the demo yet.")
    elif demo.status != DemoClass.Status.COMPLETED:
        demo.status = DemoClass.Status.COMPLETED
        demo.save(update_fields=["status"])
        messages.success(
            request,
            "Demo completed. Confirm whether you want to keep this tutor.",
        )
    else:
        messages.info(request, "This demo is already completed.")

    return redirect("tuitions:demo_classes")


@login_required
@require_POST
def confirm_tutor(request, application_id):
    if not is_student(request.user):
        raise PermissionDenied

    application = get_object_or_404(
        TuitionApplication.objects.select_related("tuition"),
        pk=application_id,
        tuition__student=request.user,
        status=TuitionApplication.Status.ACCEPTED,
    )

    demo = _demo_for_application(application)
    if not demo or demo.status != DemoClass.Status.COMPLETED:
        messages.error(request, "Complete the demo before confirming the tutor.")
        return redirect("tuitions:demo_classes")

    post = application.tuition
    if post.status == "COMPLETED":
        messages.info(request, "This tuition is already completed.")
    else:
        post.status = "COMPLETED"
        post.save(update_fields=["status"])
        messages.success(
            request,
            "Tutor confirmed. Tuition completed; you can now submit a review.",
        )

    return redirect("tuitions:demo_classes")


@login_required
@require_POST
def decline_tutor(request, application_id):
    if not is_student(request.user):
        raise PermissionDenied

    with transaction.atomic():
        application = get_object_or_404(
            TuitionApplication.objects.select_related("tuition"),
            pk=application_id,
            tuition__student=request.user,
            status=TuitionApplication.Status.ACCEPTED,
        )

        demo = _demo_for_application(application)
        if not demo or demo.status != DemoClass.Status.COMPLETED:
            messages.error(
                request,
                "Complete the demo before choosing another tutor.",
            )
            return redirect("tuitions:demo_classes")

        post = TuitionPost.objects.select_for_update().get(
            pk=application.tuition_id
        )
        application.status = TuitionApplication.Status.REJECTED
        application.save(update_fields=["status"])

        post.status = "CLOSED" if post.target_tutor_id else "OPEN"
        post.save(update_fields=["status"])

    messages.success(
        request,
        "Tutor declined. You can post a new request if needed.",
    )
    return redirect("tuitions:post_list")


@login_required
@require_POST
def submit_review(request, application_id):
    if not is_student(request.user):
        raise PermissionDenied

    application = get_object_or_404(
        TuitionApplication.objects.select_related("tuition"),
        pk=application_id,
        tuition__student=request.user,
        status=TuitionApplication.Status.ACCEPTED,
    )

    demo = _demo_for_application(application)
    if not demo or demo.status != DemoClass.Status.COMPLETED:
        messages.error(request, "Complete the demo before submitting a review.")
        return redirect("tuitions:demo_classes")

    if application.reviewed_at:
        messages.info(request, "You have already submitted a review.")
        return redirect("tuitions:demo_classes")

    form = TuitionReviewForm(request.POST, instance=application)
    if not form.is_valid():
        messages.error(request, "Please select a rating from 1 to 5.")
        return redirect("tuitions:demo_classes")

    review = form.save(commit=False)
    review.reviewed_at = timezone.now()
    review.save()

    ratings = list(
        TuitionApplication.objects.filter(
            tutor=application.tutor,
            reviewed_at__isnull=False,
        ).exclude(
            review_rating__isnull=True
        ).values_list("review_rating", flat=True)
    )

    profile = TutorProfile.objects.filter(user=application.tutor).first()
    if profile:
        profile.review_count = len(ratings)
        profile.rating = (
            round(sum(ratings) / len(ratings), 1) if ratings else 0
        )
        profile.save(update_fields=["rating", "review_count"])

    messages.success(request, "Your review has been submitted successfully.")
    return redirect("tuitions:demo_classes")