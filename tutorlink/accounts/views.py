from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import User, VerificationDocument
from .forms import UserProfileForm, TutorProfileForm
from tutors.models import TutorProfile


def login_view(request):
    if request.user.is_authenticated:
        return redirect("role_dashboard")

    if request.method == "POST":
        username = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", "STUDENT").upper().strip()

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None:
            account = User.objects.filter(
                email__iexact=username
            ).first()

            if account:
                user = authenticate(
                    request,
                    username=account.username,
                    password=password,
                )

        if user is None:
            messages.error(
                request,
                "Invalid username or password.",
            )
            return render(request, "accounts/login.html")

        if not user.is_active:
            messages.error(request, "Your account is inactive.")
            return render(request, "accounts/login.html")

        actual_role = "ADMIN" if user.is_superuser else user.role

        if role != actual_role:
            messages.error(
                request,
                "Please select the correct role.",
            )
            return render(request, "accounts/login.html")

        if role == "ADMIN" and not user.is_staff:
            messages.error(
                request,
                "You do not have admin access.",
            )
            return render(request, "accounts/login.html")

        login(request, user)
        return redirect("role_dashboard")

    return render(request, "accounts/login.html")


@login_required
def role_dashboard(request):
    user = request.user
    role = "ADMIN" if user.is_superuser else user.role

    if role == "ADMIN":
        return redirect("/admin/")

    if role == "TUTOR":
        return redirect("tutor_dashboard")

    return redirect("student_dashboard")


@login_required
def student_dashboard(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("role_dashboard")

    return render(
        request,
        "accounts/dashboards/student_dashboard.html",
        {
            "user": request.user,
            "role_name": "Student",
            "location": "Dhanmondi, Dhaka",
            "badges": {
                "applications": 2,
                "demos": 1,
                "messages": 2,
            },
        },
    )


@login_required
def tutor_dashboard(request):
    if request.user.role != User.Role.TUTOR:
        return redirect("role_dashboard")

    return render(
        request,
        "accounts/dashboards/tutor_dashboard.html",
        {
            "user": request.user,
            "role_name": "Tutor",
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("role_dashboard")

    if request.method == "POST":
        role = request.POST.get(
            "role", "STUDENT"
        ).upper().strip()

        name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get(
            "confirm_password", ""
        )

        if role not in ["STUDENT", "TUTOR"]:
            messages.error(
                request,
                "Please select Student or Tutor.",
            )

        elif not name or not email or not password:
            messages.error(
                request,
                "Please fill in all required fields.",
            )

        elif password != confirm_password:
            messages.error(
                request,
                "Passwords do not match.",
            )

        elif (
            User.objects.filter(
                username__iexact=email
            ).exists()
            or User.objects.filter(
                email__iexact=email
            ).exists()
        ):
            messages.error(
                request,
                "This username or email already exists.",
            )

        else:
            names = name.split()

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=names[0],
                last_name=" ".join(names[1:]),
                role=role,
                phone=request.POST.get("phone", "").strip(),
                division=request.POST.get(
                    "division", "Dhaka"
                ).strip(),
                district=request.POST.get(
                    "district", "Dhaka"
                ).strip(),
                area=request.POST.get("area", "").strip(),
                bio=request.POST.get("bio", "").strip(),
            )

            if role == "STUDENT":
                user.institution = request.POST.get(
                    "institution", ""
                ).strip()

                user.academic_level = request.POST.get(
                    "academic_level", ""
                ).strip()

                budget = request.POST.get(
                    "monthly_budget", ""
                ).strip()

                if budget:
                    user.monthly_budget = budget

            if "profile_picture" in request.FILES:
                user.profile_picture = request.FILES[
                    "profile_picture"
                ]

            user.save()

            # Create a tutor profile when a tutor registers.
            if role == "TUTOR":
                TutorProfile.objects.get_or_create(user=user)

            login(request, user)

            messages.success(
                request,
                "Account created successfully!",
            )
            return redirect("verify_identity")

    return render(request, "accounts/register.html")


@login_required
def verify_identity_view(request):
    if request.user.is_superuser:
        return redirect("/admin/")

    documents = VerificationDocument.objects.filter(
        user=request.user
    ).order_by("-submitted_at")

    if (
        request.method == "POST"
        and "document_file" in request.FILES
    ):
        if documents.filter(
            status=VerificationDocument.Status.PENDING
        ).exists():
            messages.warning(
                request,
                "A document is already under review.",
            )
        else:
            VerificationDocument.objects.create(
                user=request.user,
                doc_type=request.POST.get(
                    "doc_type",
                    VerificationDocument.DocType.STUDENT_ID,
                ),
                file=request.FILES["document_file"],
                status=VerificationDocument.Status.PENDING,
            )

            messages.success(
                request,
                "Document submitted successfully!",
            )

        return redirect("verify_identity")

    return render(
        request,
        "accounts/verify_identity.html",
        {
            "user_documents": documents,
            "has_pending": documents.filter(
                status=VerificationDocument.Status.PENDING
            ).exists(),
            "is_approved": documents.filter(
                status=VerificationDocument.Status.APPROVED
            ).exists(),
        },
    )


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


@login_required
def profile_view(request):
    user = request.user
    tutor_profile = None

    if user.role == User.Role.TUTOR:
        tutor_profile, _ = TutorProfile.objects.get_or_create(
            user=user
        )

        tutor_profile = (
            TutorProfile.objects
            .select_related("user")
            .prefetch_related("subjects")
            .get(pk=tutor_profile.pk)
        )

    role_name = (
        "Administrator"
        if user.is_superuser
        else user.get_role_display()
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_user": user,
            "tutor_profile": tutor_profile,
            "role_name": role_name,
        },
    )


@login_required
def edit_profile(request):
    user = request.user
    tutor_profile = None

    if user.role == User.Role.TUTOR:
        tutor_profile, _ = TutorProfile.objects.get_or_create(
            user=user
        )

    if request.method == "POST":
        user_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=user,
        )

        tutor_form = (
            TutorProfileForm(
                request.POST,
                instance=tutor_profile,
            )
            if tutor_profile is not None
            else None
        )

        user_valid = user_form.is_valid()
        tutor_valid = (
            tutor_form.is_valid()
            if tutor_form is not None
            else True
        )

        if user_valid and tutor_valid:
            user_form.save()

            if tutor_form is not None:
                tutor_form.save()

            messages.success(
                request,
                "Your profile has been updated successfully.",
            )
            return redirect("profile")

    else:
        user_form = UserProfileForm(instance=user)

        tutor_form = (
            TutorProfileForm(instance=tutor_profile)
            if tutor_profile is not None
            else None
        )

    role_name = (
        "Administrator"
        if user.is_superuser
        else user.get_role_display()
    )

    return render(
        request,
        "accounts/edit_profile.html",
        {
            "user_form": user_form,
            "tutor_form": tutor_form,
            "role_name": role_name,
        },
    )