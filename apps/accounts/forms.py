from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="密碼",
        strip=False,
        help_text="至少 8 個字元，避免使用常見或純數字密碼。",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="確認密碼",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("account", "phone")
        widgets = {
            "account": forms.TextInput(attrs={"autocomplete": "username"}),
            "phone": forms.TelInput(attrs={"autocomplete": "tel", "placeholder": "請輸入聯絡電話"}),
        }

    def clean_account(self):
        account = self.cleaned_data["account"].strip()
        if User.objects.filter(account=account).exists():
            raise ValidationError("這個帳號已經註冊過了。")
        return account

    def clean(self):
        cleaned_data = super().clean()
        password1, password2 = cleaned_data.get("password1"), cleaned_data.get("password2")
        if password1 and password2:
            if password1 != password2:
                self.add_error("password2", "兩次輸入的密碼不一致。")
            else:
                candidate = User(
                    account=cleaned_data.get("account", ""),
                    phone=cleaned_data.get("phone", ""),
                )
                validate_password(password1, candidate)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
