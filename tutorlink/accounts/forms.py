from django import forms

from .models import User
from tutors.models import Subject, TutorProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "profile_picture",
            "bio",
            "division",
            "district",
            "area",
            "institution",
            "academic_level",
            "monthly_budget",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
            "profile_picture": forms.ClearableFileInput(
                attrs={"accept": "image/*"}
            ),
            "monthly_budget": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "1",
                    "placeholder": "Monthly budget",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

        # Student-only fields should not appear for tutors or admins.
        if self.instance and self.instance.role != User.Role.STUDENT:
            for field in (
                "institution",
                "academic_level",
                "monthly_budget",
            ):
                self.fields.pop(field, None)

    def clean_email(self):
        email = self.cleaned_data["email"].strip()

        email_exists = User.objects.filter(
            email__iexact=email
        ).exclude(pk=self.instance.pk)

        username_exists = User.objects.filter(
            username__iexact=email
        ).exclude(pk=self.instance.pk)

        if email_exists.exists() or username_exists.exists():
            raise forms.ValidationError(
                "This email is already being used."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data["email"].strip()

        # Existing project login uses email as the username.
        user.username = user.email

        if commit:
            user.save()
            self.save_m2m()

        return user


class TutorProfileForm(forms.ModelForm):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select all subjects you are confident teaching.",
    )

    class Meta:
        model = TutorProfile
        fields = [
            "university",
            "department",
            "subjects",
            "class_from",
            "class_to",
            "expected_salary",
            "mode",
            "experience_years",
            "available_time",
        ]
        widgets = {
            "available_time": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Sat-Thu, 4-9 PM"
                }
            ),
            "expected_salary": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "1",
                    "placeholder": "Expected monthly salary (BDT)",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        class_from = cleaned_data.get("class_from")
        class_to = cleaned_data.get("class_to")

        if (
            class_from is not None
            and class_to is not None
            and class_from > class_to
        ):
            self.add_error(
                "class_to",
                "Class To must be greater than or equal to Class From.",
            )

        return cleaned_data