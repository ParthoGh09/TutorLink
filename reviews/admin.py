from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'reviewer', 'reviewee', 'overall_rating', 'post_as_verified', 'created_at')
    list_filter = ('review_type', 'overall_rating', 'post_as_verified', 'created_at')
    search_fields = ('reviewer__username', 'reviewee__username', 'tuition_title', 'review_text')
