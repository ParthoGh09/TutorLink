from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = [
            'overall_rating',
            'subject_knowledge',
            'communication',
            'punctuality',
            'safety_and_respect',
            'review_text',
            'post_as_verified'
        ]
        widgets = {
            'overall_rating': forms.HiddenInput(),
            'subject_knowledge': forms.HiddenInput(),
            'communication': forms.HiddenInput(),
            'punctuality': forms.HiddenInput(),
            'safety_and_respect': forms.HiddenInput(),
            'review_text': forms.Textarea(attrs={
                'class': 'review-textarea',
                'placeholder': 'Share your experience with this tutor...',
                'rows': 4,
            }),
            'post_as_verified': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            })
        }


