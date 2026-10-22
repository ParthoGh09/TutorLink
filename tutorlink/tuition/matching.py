"""Smart Match scoring (class diagram: MatchResult / calculate_match()).

Weights come straight from the 'How the score works' card in the design:
subject & level 25, budget 20, location 20, availability 15, mode 10,
verification & rating 10.

The tutor profile model is owned by another teammate, so every tutor attribute
is read defensively. If a field does not exist yet, that component gets a
neutral 50% instead of crashing. Once the tutor profile exists, just make sure
one of the attribute names listed below is present (or add yours to the tuples).
"""

from dataclasses import dataclass

WEIGHTS = {
    "subject": 25,
    "budget": 20,
    "location": 20,
    "availability": 15,
    "mode": 10,
    "trust": 10,
}

NEUTRAL = 0.5

# Attribute names probed on the user, user.tutor_profile and user.profile.
SUBJECT_ATTRS = ("subjects", "subject", "teaching_subjects")
LEVEL_ATTRS = ("class_levels", "levels", "teaching_levels")
SALARY_ATTRS = ("expected_salary", "expected_fee", "monthly_rate", "salary")
AREA_ATTRS = ("area",)
DISTRICT_ATTRS = ("district",)
DIVISION_ATTRS = ("division",)
DAYS_ATTRS = ("available_days", "availability_days", "availability")
MODE_ATTRS = ("teaching_mode", "mode", "preferred_mode")
RATING_ATTRS = ("rating", "average_rating", "avg_rating")
VERIFIED_ATTRS = ("is_verified", "verified")


@dataclass
class MatchResult:
    total: int
    breakdown: dict


def get_attr(user, names, default=None):
    """First non-empty attribute found on the user or a related profile object."""
    for holder in (user, getattr(user, "tutor_profile", None), getattr(user, "profile", None)):
        if holder is None:
            continue
        for name in names:
            value = getattr(holder, name, None)
            if callable(value) and not hasattr(value, "all"):
                continue
            if value not in (None, ""):
                return value
    return default


def _as_words(value):
    """Turn a string / list / M2M manager into a lowercase set of strings."""
    if value is None:
        return set()
    if hasattr(value, "all"):
        value = [str(v) for v in value.all()]
    if isinstance(value, str):
        value = value.replace("+", ",").replace("/", ",").split(",")
    return {str(v).strip().lower() for v in value if str(v).strip()}


def _subject_score(tutor, post):
    subjects = _as_words(get_attr(tutor, SUBJECT_ATTRS))
    if not subjects:
        return NEUTRAL
    hit = any(post.subject.lower() in s or s in post.subject.lower() for s in subjects)
    score = 1.0 if hit else 0.2
    levels = _as_words(get_attr(tutor, LEVEL_ATTRS))
    if levels and hit:
        score = 1.0 if post.class_level.lower() in levels else 0.8
    return score


def _budget_score(tutor, post):
    salary = get_attr(tutor, SALARY_ATTRS)
    try:
        salary = float(salary)
    except (TypeError, ValueError):
        return NEUTRAL
    if post.budget_min <= salary <= post.budget_max:
        return 1.0
    gap = post.budget_min - salary if salary < post.budget_min else salary - post.budget_max
    return max(0.0, 1.0 - gap / max(post.budget_max, 1))


def _location_score(tutor, post):
    area = str(get_attr(tutor, AREA_ATTRS, "")).lower()
    district = str(get_attr(tutor, DISTRICT_ATTRS, "")).lower()
    division = str(get_attr(tutor, DIVISION_ATTRS, "")).lower()
    if not (area or district or division):
        return NEUTRAL
    if area and area == post.area.lower():
        return 1.0
    if district and district == post.district.lower():
        return 0.7
    if division and division == post.division.lower():
        return 0.4
    return 0.1


def _availability_score(tutor, post):
    days = {d[:3] for d in _as_words(get_attr(tutor, DAYS_ATTRS))}
    wanted = {d.lower() for d in post.days_list}
    if not days or not wanted:
        return NEUTRAL
    return len(days & wanted) / len(wanted)


def _mode_score(tutor, post):
    mode = str(get_attr(tutor, MODE_ATTRS, "")).lower()
    if not mode:
        return NEUTRAL
    if "both" in mode or ("online" in mode and "offline" in mode):
        return 1.0
    return 1.0 if mode == post.teaching_mode.lower() else 0.0


def _trust_score(tutor, post):
    verified = get_attr(tutor, VERIFIED_ATTRS)
    rating = get_attr(tutor, RATING_ATTRS)
    try:
        rating_part = min(float(rating), 5.0) / 5.0
    except (TypeError, ValueError):
        rating_part = NEUTRAL
    verified_part = 1.0 if verified else (NEUTRAL if verified is None else 0.0)
    return 0.5 * verified_part + 0.5 * rating_part


def calculate_match(tutor, post) -> MatchResult:
    parts = {
        "subject": _subject_score(tutor, post),
        "budget": _budget_score(tutor, post),
        "location": _location_score(tutor, post),
        "availability": _availability_score(tutor, post),
        "mode": _mode_score(tutor, post),
        "trust": _trust_score(tutor, post),
    }
    total = sum(parts[k] * WEIGHTS[k] for k in parts)
    return MatchResult(
        total=round(total),
        breakdown={k: round(v * 100) for k, v in parts.items()},
    )


def find_matching_tutors(post, limit=10, min_score=70):
    """Used when a post is published ('Smart Match will run automatically').

    Returns [(tutor, score), ...] best first. Hook your Notification model in
    here once it exists (NotificationType.MATCH).
    """
    from django.contrib.auth import get_user_model
    from django.core.exceptions import FieldError

    User = get_user_model()
    try:
        tutors = User.objects.filter(role__iexact="TUTOR")
    except FieldError:
        return []
    scored = [(t, calculate_match(t, post).total) for t in tutors]
    scored = [s for s in scored if s[1] >= min_score]
    scored.sort(key=lambda s: s[1], reverse=True)
    return scored[:limit]
