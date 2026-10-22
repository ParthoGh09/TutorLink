from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.views import get_effective_role, role_required

from .constants import CLASS_LEVELS, DAYS, LOCATIONS, SUBJECTS, TIME_SLOTS
from .forms import ApplicationForm, CommentForm, TuitionPostForm
from .matching import calculate_match, find_matching_tutors, get_attr
from .models import Application, Comment, SavedPost, TuitionPost

PAGE_SIZE = 4  # the design shows four cards, then "Load More"
BUDGET_FLOOR, BUDGET_CEIL = 3000, 10000


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def user_role(user):
    """Same rule the accounts app uses (superusers count as ADMIN)."""
    return str(get_effective_role(user))


def is_verified(user):
    """Admin-approved identity (User.is_verified, set from the admin panel)."""
    return bool(user.is_verified)


def ctx(request, **extra):
    base = {
        "home_url": reverse("role_dashboard"),
        "role": user_role(request.user),
    }
    base.update(extra)
    return base


def location_data():
    return LOCATIONS


# --------------------------------------------------------------------------
# Screen 09 – Create Tuition Post  (student)
# --------------------------------------------------------------------------
@role_required("STUDENT")
def create_post(request):
    form = TuitionPostForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.student = request.user
        saving_draft = "save_draft" in request.POST
        post.status = TuitionPost.Status.DRAFT if saving_draft else TuitionPost.Status.OPEN
        post.save()
        if saving_draft:
            messages.success(request, "Draft saved. You can publish it later from My Posts.")
            return redirect("tuition:my_posts")
        matches = find_matching_tutors(post)
        if matches:
            messages.success(
                request, f"Post published. Smart Match found {len(matches)} tutors for you."
            )
        else:
            messages.success(request, "Post published. Smart Match will notify the best tutors.")
        return redirect(post)

    mine = request.user.tuition_posts
    stats = {
        "active": mine.filter(status=TuitionPost.Status.OPEN).count(),
        "applicants": Application.objects.filter(post__student=request.user).count(),
    }
    return render(
        request,
        "tuition/create_post.html",
        ctx(
            request,
            form=form,
            stats=stats,
            subjects=SUBJECTS,
            class_levels=CLASS_LEVELS,
            days=DAYS,
            time_slots=TIME_SLOTS,
            post_types=TuitionPost.PostType.choices,
            locations=location_data(),
            selected_days=request.POST.getlist("preferred_days") if request.method == "POST" else ["Sat", "Mon", "Wed"],
            mode=request.POST.get("teaching_mode", "ONLINE"),
        ),
    )


@role_required("STUDENT")
def my_posts(request):
    posts = (
        request.user.tuition_posts.annotate(applicant_count=Count("applications", distinct=True))
        .order_by("-created_at")
    )
    return render(request, "tuition/my_posts.html", ctx(request, posts=posts))


@role_required("STUDENT")
@require_POST
def change_status(request, pk):
    post = get_object_or_404(TuitionPost, pk=pk, student=request.user)
    action = request.POST.get("action")
    new = {
        "publish": TuitionPost.Status.OPEN,
        "reopen": TuitionPost.Status.OPEN,
        "pause": TuitionPost.Status.PAUSED,
        "close": TuitionPost.Status.CLOSED,
    }.get(action)
    if new:
        post.status = new
        post.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Post is now {post.get_status_display().lower()}.")
    return redirect("tuition:my_posts")


# --------------------------------------------------------------------------
# Screen 10 – Find Tuition  (tutor)
# --------------------------------------------------------------------------
def _profile_completeness(user):
    checks = [
        user.first_name or user.last_name,
        user.email,
        get_attr(user, ("phone", "phone_number")),
        get_attr(user, ("bio", "about")),
        get_attr(user, ("institution", "university")),
        get_attr(user, ("subjects", "subject")),
        get_attr(user, ("expected_salary", "expected_fee")),
        get_attr(user, ("available_days", "availability")),
        get_attr(user, ("profile_picture", "photo")),
    ]
    return round(100 * sum(1 for c in checks if c) / len(checks))


@role_required("TUTOR")
def find_tuition(request):
    g = request.GET
    tab = g.get("tab", "posts")
    submitted = "f" in g  # hidden marker so unchecked boxes are understood

    f = {
        "q": g.get("q", "").strip(),
        "subject": g.get("subject", ""),
        "class_level": g.get("class_level", ""),
        "division": g.get("division", ""),
        "district": g.get("district", ""),
        "area": g.get("area", ""),
        "modes": g.getlist("mode") if submitted else ["ONLINE", "OFFLINE"],
        "open_only": (g.get("open_only") == "1") if submitted else True,
        "include_paused": (g.get("include_paused") == "1") if submitted else False,
        "sort": g.get("sort", "match"),
    }
    try:
        f["min_budget"] = max(BUDGET_FLOOR, int(g.get("min_budget", BUDGET_FLOOR)))
        f["max_budget"] = min(BUDGET_CEIL, int(g.get("max_budget", BUDGET_CEIL)))
    except ValueError:
        f["min_budget"], f["max_budget"] = BUDGET_FLOOR, BUDGET_CEIL

    base = TuitionPost.objects.exclude(status=TuitionPost.Status.DRAFT).select_related("student")

    # my applications tab is a separate list
    my_apps = Application.objects.filter(tutor=request.user).select_related("post", "post__student")
    open_total = TuitionPost.objects.filter(status=TuitionPost.Status.OPEN).count()

    posts = base.annotate(comment_count=Count("comments", distinct=True))
    if f["open_only"]:
        statuses = [TuitionPost.Status.OPEN]
        if f["include_paused"]:
            statuses.append(TuitionPost.Status.PAUSED)
        posts = posts.filter(status__in=statuses)
    else:
        posts = posts.all()

    if f["q"]:
        from django.db.models import Q

        posts = posts.filter(
            Q(subject__icontains=f["q"]) | Q(class_level__icontains=f["q"])
            | Q(area__icontains=f["q"]) | Q(description__icontains=f["q"])
        )
    for field in ("subject", "class_level", "division", "district", "area"):
        if f[field]:
            posts = posts.filter(**{field: f[field]})
    if f["modes"] and set(f["modes"]) != {"ONLINE", "OFFLINE"}:
        posts = posts.filter(teaching_mode__in=f["modes"])
    posts = posts.filter(budget_max__gte=f["min_budget"])
    if f["max_budget"] < BUDGET_CEIL:  # 10,000+ means "no upper limit"
        posts = posts.filter(budget_min__lte=f["max_budget"])
    if tab == "saved":
        posts = posts.filter(saved_by__tutor=request.user)

    scored = [(p, calculate_match(request.user, p).total) for p in posts]
    if tab == "recommended":
        scored = [s for s in scored if s[1] >= 80]
    if f["sort"] == "newest":
        scored.sort(key=lambda s: s[0].created_at, reverse=True)
    elif f["sort"] == "budget":
        scored.sort(key=lambda s: s[0].budget_max, reverse=True)
    else:
        scored.sort(key=lambda s: (s[1], s[0].created_at), reverse=True)

    total = len(scored)
    try:
        limit = max(PAGE_SIZE, int(g.get("limit", PAGE_SIZE)))
    except ValueError:
        limit = PAGE_SIZE
    visible = scored[:limit]
    more_url = None
    if total > limit:
        q = g.copy()
        q["limit"] = limit + PAGE_SIZE
        more_url = "?" + q.urlencode()

    applied_ids = set(my_apps.values_list("post_id", flat=True))
    saved_ids = set(request.user.saved_tuition_posts.values_list("post_id", flat=True))

    matched_for_you = sum(
        1 for p in TuitionPost.objects.filter(status=TuitionPost.Status.OPEN)
        if calculate_match(request.user, p).total >= 80
    )

    return render(
        request,
        "tuition/find_tuition.html",
        ctx(
            request,
            tab=tab,
            f=f,
            cards=visible,
            total=total,
            more_url=more_url,
            applied_ids=applied_ids,
            saved_ids=saved_ids,
            my_apps=my_apps,
            side_apps=my_apps[:3],
            open_total=open_total,
            matched_for_you=matched_for_you,
            completeness=_profile_completeness(request.user),
            subjects=SUBJECTS,
            class_levels=CLASS_LEVELS,
            locations=location_data(),
            budget_floor=BUDGET_FLOOR,
            budget_ceil=BUDGET_CEIL,
            tutor_institution=get_attr(request.user, ("institution", "university"), ""),
            tutor_department=get_attr(request.user, ("department", "major"), ""),
            tutor_rating=get_attr(request.user, ("rating", "average_rating"), None),
        ),
    )


@role_required("TUTOR")
@require_POST
def toggle_save(request, pk):
    post = get_object_or_404(TuitionPost, pk=pk)
    obj, created = SavedPost.objects.get_or_create(tutor=request.user, post=post)
    if not created:
        obj.delete()
    return redirect(request.POST.get("next") or "tuition:find_tuition")


# --------------------------------------------------------------------------
# Screen 11 – Tuition Post Detail  (student + tutor)
# --------------------------------------------------------------------------
@role_required("STUDENT", "TUTOR", "ADMIN")
def post_detail(request, pk):
    post = get_object_or_404(TuitionPost.objects.select_related("student"), pk=pk)
    role = user_role(request.user)
    is_owner = post.student_id == request.user.pk

    # drafts are private to their author
    if post.status == TuitionPost.Status.DRAFT and not is_owner:
        raise PermissionDenied

    top_comments = (
        post.comments.filter(parent__isnull=True)
        .select_related("author")
        .prefetch_related("replies__author")
    )

    application = None
    match = None
    if role == "TUTOR":
        application = Application.objects.filter(post=post, tutor=request.user).first()
        match = calculate_match(request.user, post)

    can_apply = (
        role == "TUTOR" and application is None and post.status == TuitionPost.Status.OPEN
    )
    return render(
        request,
        "tuition/post_detail.html",
        ctx(
            request,
            post=post,
            is_owner=is_owner,
            comments=top_comments,
            comment_count=post.comments.count(),
            comment_form=CommentForm(),
            application=application,
            match=match,
            can_apply=can_apply,
            verified=is_verified(request.user),
            student_level=post.class_level,
            student_school=get_attr(post.student, ("institution", "school"), ""),
        ),
    )


@role_required("TUTOR")
@require_POST
def apply(request, pk):
    post = get_object_or_404(TuitionPost, pk=pk)
    if post.status != TuitionPost.Status.OPEN:
        messages.error(request, "This post is not open for applications.")
        return redirect(post)
    if not is_verified(request.user):
        messages.error(request, "Your identity must be verified before you can apply.")
        return redirect(post)
    form = ApplicationForm(request.POST)
    if form.is_valid():
        _, created = Application.objects.get_or_create(
            post=post,
            tutor=request.user,
            defaults={
                "message": form.cleaned_data["message"].strip(),
                "match_score": calculate_match(request.user, post).total,
            },
        )
        if created:
            messages.success(request, "Application sent. Next step: request one online demo class.")
        else:
            messages.info(request, "You have already applied to this post.")
    return redirect(post)


@login_required
@require_POST
def add_comment(request, pk):
    post = get_object_or_404(TuitionPost, pk=pk)
    if post.status == TuitionPost.Status.DRAFT:
        raise PermissionDenied
    form = CommentForm(request.POST)
    if form.is_valid():
        parent = None
        parent_id = request.POST.get("parent")
        if parent_id:
            parent = get_object_or_404(Comment, pk=parent_id, post=post)
            parent = parent.parent or parent  # replies stay one level deep
        Comment.objects.create(
            post=post, author=request.user, parent=parent, body=form.cleaned_data["body"]
        )
    else:
        messages.error(request, "Write something before posting.")
    return redirect(f"{post.get_absolute_url()}#discussion")


@login_required
@require_POST
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment.body = form.cleaned_data["body"]
        comment.edited = True
        comment.save(update_fields=["body", "edited"])
    return redirect(f"{comment.post.get_absolute_url()}#comment-{comment.pk}")


@login_required
@require_POST
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.author_id != request.user.pk and user_role(request.user) != "ADMIN":
        raise PermissionDenied
    post = comment.post
    comment.delete()
    return redirect(f"{post.get_absolute_url()}#discussion")
