import re

from django import forms

from .constants import CLASS_LEVELS, DAYS, LOCATIONS, SUBJECTS, TIME_SLOTS
from .models import Application, Comment, TuitionPost


class TuitionPostForm(forms.ModelForm):
    """Screen 09. Fields are rendered by hand in the template to match the design."""

    budget = forms.CharField(max_length=40)
    preferred_days = forms.MultipleChoiceField(
        choices=[(d, d) for d in DAYS],
        error_messages={"required": "Pick at least one day."},
    )

    class Meta:
        model = TuitionPost
        fields = [
            "subject", "class_level", "post_type", "division", "district", "area",
            "time_slot", "teaching_mode", "description",
        ]

    def clean_subject(self):
        subject = self.cleaned_data["subject"]
        if subject not in SUBJECTS:
            raise forms.ValidationError("Choose a subject from the list.")
        return subject

    def clean_class_level(self):
        level = self.cleaned_data["class_level"]
        if level not in CLASS_LEVELS:
            raise forms.ValidationError("Choose a class level from the list.")
        return level

    def clean_time_slot(self):
        slot = self.cleaned_data["time_slot"]
        if slot not in TIME_SLOTS:
            raise forms.ValidationError("Choose a time from the list.")
        return slot

    def clean_budget(self):
        raw = self.cleaned_data["budget"]
        numbers = [int(n) for n in re.findall(r"\d+", raw.replace(",", ""))]
        if not numbers or len(numbers) > 2:
            raise forms.ValidationError("Enter a budget like 6000 or 6,000 – 8,000.")
        low, high = (numbers[0], numbers[0]) if len(numbers) == 1 else sorted(numbers)
        if low <= 0:
            raise forms.ValidationError("Budget must be greater than zero.")
        return low, high

    def clean_description(self):
        text = self.cleaned_data["description"].strip()
        if len(text) < 20:
            raise forms.ValidationError("Tell tutors a little more (at least 20 characters).")
        return text

    def clean(self):
        data = super().clean()
        division, district, area = data.get("division"), data.get("district"), data.get("area")
        if division and district and area:
            if area not in LOCATIONS.get(division, {}).get(district, []):
                self.add_error("area", "Choose a valid division, district and area.")
        return data

    def save(self, commit=True):
        post = super().save(commit=False)
        post.budget_min, post.budget_max = self.cleaned_data["budget"]
        post.preferred_days = ",".join(self.cleaned_data["preferred_days"])
        if commit:
            post.save()
        return post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("Write something first.")
        return body


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["message"]
