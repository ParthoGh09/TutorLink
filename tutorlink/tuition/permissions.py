"""Role helpers for the tuition app.

These mirror accounts.views.get_effective_role / role_required, but live here so the
tuition app still imports even if the accounts app changes or is on an older branch.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def get_effective_role(user):
    """Superusers count as ADMIN; everyone else uses User.role."""
    if user.is_superuser:
        return "ADMIN"
    return str(getattr(user, "role", "") or "").strip().upper()


def role_required(*allowed_roles):
    """Login + role check. Wrong-role users go back to their own dashboard."""
    allowed = {str(r).upper() for r in allowed_roles}

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if get_effective_role(request.user) not in allowed:
                messages.error(request, "You do not have permission to access that page.")
                return redirect("role_dashboard")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
