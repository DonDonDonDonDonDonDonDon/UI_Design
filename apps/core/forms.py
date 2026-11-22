from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ("category", "message", "contact")
        widgets = {
            "message": forms.Textarea(attrs={"maxlength": 1000, "rows": 5}),
            "contact": forms.TextInput(attrs={"maxlength": 120}),
        }
