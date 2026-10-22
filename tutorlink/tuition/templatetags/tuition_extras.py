from django import template

register = template.Library()


def _role(user):
    if getattr(user, "is_superuser", False):
        return "admin"
    return str(getattr(user, "role", "") or "").strip().lower()


@register.filter
def display_name(user):
    full = user.get_full_name() if hasattr(user, "get_full_name") else ""
    return full or getattr(user, "username", str(user))


@register.filter
def initials(user):
    parts = display_name(user).split()
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


@register.filter
def avatar_tone(user):
    """0-4, picks one of the pastel avatar colours from the palette."""
    return (getattr(user, "pk", 0) or 0) % 5


@register.filter
def role_label(user):
    return _role(user).capitalize() if _role(user) else "Member"


@register.filter
def is_role(user, role):
    return _role(user).upper() == str(role).upper()


@register.filter
def match_tone(score):
    """Green ring for strong matches, amber otherwise (as in the design)."""
    try:
        return "good" if int(score) >= 85 else "fair"
    except (TypeError, ValueError):
        return "fair"


@register.filter
def short_status(value):
    return str(value).replace("_", " ").capitalize()


@register.simple_tag
def user_area(user):
    for holder in (user, getattr(user, "profile", None), getattr(user, "student_profile", None)):
        if holder is None:
            continue
        area = getattr(holder, "area", None)
        district = getattr(holder, "district", None)
        if area and district:
            return f"{area}, {district}"
        if area:
            return area
    return "Dhanmondi, Dhaka"


@register.filter
def ago(value):
    """'2 hours, 14 minutes' -> '2 hours ago' (design uses the single largest unit)."""
    from django.utils.timesince import timesince

    text = timesince(value).split(",")[0].replace("\xa0", " ")
    if text.startswith("0 minute"):
        return "just now"
    return f"{text} ago"
