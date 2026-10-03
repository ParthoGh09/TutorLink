from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import User, VerificationDocument


def get_effective_role(user):
    """Return the role used by the application for routing/authorization."""
    if user.is_superuser:
        return User.Role.ADMIN
    return user.role


def role_required(*allowed_roles):
    """Protect a view so users can only access their own role area."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if get_effective_role(request.user) not in allowed_roles:
                messages.error(request, "You do not have permission to access that page.")
                return redirect('role_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def login_view(request):
    # Already logged-in users should never be sent back to verification/login.
    if request.user.is_authenticated:
        return redirect('role_dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        selected_role = request.POST.get('role', User.Role.STUDENT).upper().strip()

        valid_roles = {choice[0] for choice in User.Role.choices}
        if selected_role not in valid_roles:
            messages.error(request, "Please select a valid account role.")
            return render(request, 'accounts/login.html', {'selected_role': User.Role.STUDENT})

        if not identifier or not password:
            messages.error(request, "Please enter your username/email and password.")
            return render(request, 'accounts/login.html', {'selected_role': selected_role})

        # The project uses username=email for registered accounts, but this also
        # supports users created directly from Django Admin with a different username.
        user = authenticate(request, username=identifier, password=password)

        if user is None:
            user_obj = User.objects.filter(email__iexact=identifier).first()
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)

        if user is None:
            messages.error(request, "Invalid username/email or password.")
            return render(request, 'accounts/login.html', {'selected_role': selected_role})

        if not user.is_active:
            messages.error(request, "This account is inactive. Please contact an administrator.")
            return render(request, 'accounts/login.html', {'selected_role': selected_role})

        actual_role = get_effective_role(user)
        if actual_role != selected_role:
            messages.error(
                request,
                f"This account is registered as {user.get_role_display() if not user.is_superuser else 'Administrator'}. "
                f"Please select the {dict(User.Role.choices)[actual_role]} login tab."
            )
            return render(request, 'accounts/login.html', {'selected_role': selected_role})

        login(request, user)
        return redirect('role_dashboard')

    return render(request, 'accounts/login.html', {'selected_role': User.Role.STUDENT})


def role_dashboard(request):
    """Route an authenticated user to the dashboard for their effective role."""
    if not request.user.is_authenticated:
        return redirect('login')

    role = get_effective_role(request.user)
    if role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    if role == User.Role.TUTOR:
        return redirect('tutor_dashboard')
    return redirect('student_dashboard')


@role_required(User.Role.STUDENT)
def student_dashboard(request):
    context = {
        'user': request.user,
        'role_name': 'Student',
    }
    return render(request, 'accounts/dashboards/student_dashboard.html', context)


@role_required(User.Role.TUTOR)
def tutor_dashboard(request):
    context = {
        'user': request.user,
        'role_name': 'Tutor',
    }
    return render(request, 'accounts/dashboards/tutor_dashboard.html', context)


@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    context = {
        'user': request.user,
        'role_name': 'Administrator',
        'total_users': User.objects.count(),
        'students': User.objects.filter(role=User.Role.STUDENT).count(),
        'tutors': User.objects.filter(role=User.Role.TUTOR).count(),
        'pending_verifications': VerificationDocument.objects.filter(
            status=VerificationDocument.Status.PENDING
        ).count(),
    }
    return render(request, 'accounts/dashboards/admin_dashboard.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('role_dashboard')

    if request.method == 'POST':
        role = request.POST.get('role', User.Role.STUDENT).upper().strip()

        # Public registration is intentionally limited to Student/Tutor.
        if role not in {User.Role.STUDENT, User.Role.TUTOR}:
            messages.error(request, "Administrator accounts can only be created from the Django admin panel.")
            return render(request, 'accounts/register.html')

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        phone = request.POST.get('phone', '').strip()
        division = request.POST.get('division', 'Dhaka').strip()
        district = request.POST.get('district', 'Dhaka').strip()
        area = request.POST.get('area', '').strip()
        bio = request.POST.get('bio', '').strip()

        if not full_name or not email:
            messages.error(request, "Full name and email are required.")
            return render(request, 'accounts/register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'accounts/register.html')

        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'accounts/register.html')

        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ''
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone=phone,
            division=division,
            district=district,
            area=area,
            bio=bio,
        )

        if role == User.Role.STUDENT:
            user.institution = request.POST.get('institution', '').strip()
            user.academic_level = request.POST.get('academic_level', '').strip()
            budget = request.POST.get('monthly_budget', '').strip()
            if budget:
                user.monthly_budget = budget

        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        user.save()

        login(request, user)
        messages.success(request, "Account created successfully! Upload ID documents to complete verification.")
        return redirect('verify_identity')

    return render(request, 'accounts/register.html')


@login_required
def verify_identity_view(request):
    # Admins do not need to upload their own verification documents.
    if get_effective_role(request.user) == User.Role.ADMIN:
        return redirect('admin_dashboard')

    user = request.user
    user_documents = VerificationDocument.objects.filter(user=user).order_by('-submitted_at')

    if request.method == 'POST' and 'document_file' in request.FILES:
        doc_type = request.POST.get('doc_type', VerificationDocument.DocType.STUDENT_ID)
        doc_file = request.FILES['document_file']

        # Avoid creating duplicate pending submissions for the same account.
        if user_documents.filter(status=VerificationDocument.Status.PENDING).exists():
            messages.warning(request, "You already have a document under review.")
            return redirect('verify_identity')

        VerificationDocument.objects.create(
            user=user,
            doc_type=doc_type,
            file=doc_file,
            status=VerificationDocument.Status.PENDING,
        )
        messages.success(request, "Document submitted successfully! An admin will review it soon.")
        return redirect('verify_identity')

    context = {
        'user_documents': user_documents,
        'has_pending': user_documents.filter(status=VerificationDocument.Status.PENDING).exists(),
        'is_approved': user_documents.filter(status=VerificationDocument.Status.APPROVED).exists(),
    }
    return render(request, 'accounts/verify_identity.html', context)


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')