from django import forms
from django.utils import timezone

from .models import TuitionPost, TuitionApplication


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

    def clean(self):
        cleaned_data = super().clean()

        minimum = cleaned_data.get("budget_min")
        maximum = cleaned_data.get("budget_max")

        if (
            minimum is not None
            and maximum is not None
            and minimum > maximum
        ):
            raise forms.ValidationError(
                "Minimum budget cannot be greater than maximum budget."
            )

        return cleaned_data


class DemoScheduleForm(forms.Form):
    PLATFORM_CHOICES = [
        ("MEET", "Google Meet"),
        ("ZOOM", "Zoom"),
    ]

    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )

    time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time"})
    )

    platform = forms.ChoiceField(
        choices=PLATFORM_CHOICES
    )

    meeting_link = forms.URLField(
        widget=forms.URLInput(
            attrs={
                "placeholder": "https://meet.google.com/..."
            }
        )
    )

    def clean_date(self):
        demo_date = self.cleaned_data["date"]

        if demo_date < timezone.localdate():
            raise forms.ValidationError(
                "Demo date cannot be in the past."
            )

        return demo_date

    def clean_meeting_link(self):
        link = self.cleaned_data["meeting_link"].strip()

        allowed = (
            "https://meet.google.com/",
            "https://zoom.us/",
            "https://www.zoom.us/",
        )

        if not link.startswith(allowed):
            raise forms.ValidationError(
                "Use a Google Meet or Zoom meeting link."
            )

        return link


class TuitionReviewForm(forms.ModelForm):
    class Meta:
        model = TuitionApplication
        fields = ["review_rating", "review_text"]

        widgets = {
            "review_rating": forms.Select(
                choices=[
                    ("", "Choose a rating"),
                    (1, "1 - Poor"),
                    (2, "2 - Fair"),
                    (3, "3 - Good"),
                    (4, "4 - Very good"),
                    (5, "5 - Excellent"),
                ]
            ),
            "review_text": forms.Textarea(
                attrs={"rows": 3}
            ),
        }

    def clean_review_rating(self):
        rating = self.cleaned_data.get("review_rating")

        if rating not in (1, 2, 3, 4, 5):
            raise forms.ValidationError(
                "Select a rating from 1 to 5."
            )

        return rating