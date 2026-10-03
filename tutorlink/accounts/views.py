
# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email_or_username = request.POST.get('email')
        password = request.POST.get('password')
        selected_role = request.POST.get('role', 'STUDENT')  # STUDENT, TUTOR, ADMIN

        user = authenticate(request, username=email_or_username, password=password)

        if user is None:
            # Check if user entered email instead of username
            from accounts.models import User
            try:
                user_obj = User.objects.get(email=email_or_username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            if user.role != selected_role and not user.is_superuser:
                messages.error(request,
                               f"This account is registered as a {user.get_role_display()}, not {selected_role}.")
            else:
                login(request, user)
                return redirect('home')
        else:
            messages.error(request, "Invalid email/username or password.")

    return render(request, 'accounts/login.html', {})
