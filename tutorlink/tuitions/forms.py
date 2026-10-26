from django import forms
from .models import TuitionPost


class TuitionPostForm(forms.ModelForm):
    class Meta:
        model = TuitionPost

        fields = [
            "subject",
            "class_level",
            "description",
            "budget_min",
            "budget_max",
            "division",
            "district",
            "area",
            "preferred_days",
            "time_slot",
            "teaching_mode",
            "image",
        ]

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "image": forms.ClearableFileInput(
                attrs={"accept": "image/*"}
            ),
        }