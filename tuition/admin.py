from django.contrib import admin

from .models import Application, DemoClass, Tutor, TuitionPost

admin.site.register(Tutor)
admin.site.register(TuitionPost)
admin.site.register(Application)
admin.site.register(DemoClass)
