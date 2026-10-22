from django.contrib import admin

from .models import Application, Comment, SavedPost, TuitionPost


@admin.register(TuitionPost)
class TuitionPostAdmin(admin.ModelAdmin):
    list_display = ("subject", "class_level", "student", "area", "teaching_mode", "status", "created_at")
    list_filter = ("status", "teaching_mode", "subject")
    search_fields = ("subject", "class_level", "area", "student__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "parent", "created_at")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("tutor", "post", "status", "match_score", "applied_at")
    list_filter = ("status",)


admin.site.register(SavedPost)
