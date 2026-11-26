from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    feedback_type = forms.ChoiceField(
        choices=(
            ("", "請選擇評價"),
            (Feedback.FeedbackType.LIKE, "按讚"),
            (Feedback.FeedbackType.DISLIKE, "倒讚"),
        ),
        widget=forms.HiddenInput,
    )

    class Meta:
        model = Feedback
        fields = ("feedback_type", "category", "message", "contact")
        widgets = {
            "message": forms.Textarea(attrs={"maxlength": 1000, "rows": 5}),
            "contact": forms.TextInput(attrs={"maxlength": 120}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("feedback_type") == Feedback.FeedbackType.FORM
            and not (cleaned_data.get("message") or "").strip()
        ):
            self.add_error("message", "意見表單請填寫回饋內容。")
        return cleaned_data
