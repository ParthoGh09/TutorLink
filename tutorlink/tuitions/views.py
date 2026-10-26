from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import TuitionPost
from .forms import TuitionPostForm


def is_admin(user):
    return (
        user.is_superuser
        or str(getattr(user, "role", "")).upper() == "ADMIN"
    )


@login_required
def post_list(request):
    posts = TuitionPost.objects.select_related("student").all()

    return render(
        request,
        "tuitions/post_list.html",
        {"posts": posts},
    )


@login_required
def create_post(request):
    form = TuitionPostForm(
        request.POST or None,
        request.FILES or None
    )

    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.student = request.user
        post.status = "OPEN"
        post.save()

        return redirect("tuitions:post_list")

    return render(
        request,
        "tuitions/post_form.html",
        {
            "form": form,
            "title": "Create Tuition Post",
        },
    )


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

        # Remove the previous picture if it was replaced or cleared.
        if old_image_name and old_image_name != new_image_name:
            if default_storage.exists(old_image_name):
                default_storage.delete(old_image_name)

        return redirect("tuitions:post_list")

    return render(
        request,
        "tuitions/post_form.html",
        {
            "form": form,
            "title": "Edit Tuition Post",
        },
    )


@login_required
@require_POST
def delete_post(request, pk):
    post = get_object_or_404(TuitionPost, pk=pk)

    if post.student_id != request.user.pk and not is_admin(request.user):
        raise PermissionDenied

    # Remove the uploaded picture before deleting the post.
    if post.image:
        post.image.delete(save=False)

    post.delete()

    return redirect("tuitions:post_list")