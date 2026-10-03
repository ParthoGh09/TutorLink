from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, VerificationDocument

class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ('TutorLink Profile Details', {
            'fields': ('role', 'is_verified', 'phone', 'division', 'district', 'area', 'institution', 'academic_level', 'monthly_budget', 'bio', 'profile_picture')
        }),
    )
    list_display = ['username', 'email', 'role', 'is_verified', 'is_staff']
    list_filter = ['role', 'is_verified', 'is_staff']

@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'doc_type', 'status', 'submitted_at']
    list_filter = ['status', 'doc_type']
    search_fields = ['user__username', 'user__email']

admin.site.register(User, CustomUserAdmin)