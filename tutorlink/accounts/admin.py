from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

@admin.register(User)
class TutorLinkUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("TutorLink", {"fields": ("role", "area", "institution", "is_verified")}),
    )
    list_display = ("username", "email", "role", "is_verified", "is_staff")
    list_filter = ("role", "is_verified", "is_staff")