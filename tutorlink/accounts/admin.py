from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ('TutorLink Role & Profile', {
            'fields': ('role', 'is_verified', 'phone', 'division', 'district', 'area', 'institution', 'academic_level', 'monthly_budget', 'bio')
        }),
    )
    list_display = ['username', 'email', 'role', 'is_verified', 'is_staff']
    list_filter = ['role', 'is_verified', 'is_staff']

admin.site.register(User, CustomUserAdmin)