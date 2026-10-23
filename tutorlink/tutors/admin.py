from django.contrib import admin
from .models import DemoClass, Subject, TutorProfile

admin.site.register(Subject)
admin.site.register(TutorProfile)
admin.site.register(DemoClass)