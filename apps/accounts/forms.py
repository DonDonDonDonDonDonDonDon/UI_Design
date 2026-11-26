import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User

ENGLISH_LETTER_PATTERN = re.compile(r"[a-zA-Z\uff21-\uff3a\uff41-\uff5a]")
PHONE_PATTERN = re.compile(
    r"^(\+?886-?|0)(9[0-9]{2}-?[0-9]{3}-?[0-9]{3}|9[0-9]{8}|[2-8][0-9]{0,2}-?[0-9]{6,8})$"
)


def validate_phone_number(value):
    phone = (value or "").strip()
    if not phone:
        raise ValidationError("請輸入聯絡電話。")
    if ENGLISH_LETTER_PATTERN.search(phone):
        raise ValidationError("電話號碼不可包含英文字母。")
    if not PHONE_PATTERN.match(phone):
        raise ValidationError("請輸入有效的電話號碼（例如：0912345678 或 02-12345678）。")
    return phone


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
        fields = ("account", "name", "group_name", "phone")
        help_texts = {
            "phone": "請輸入有效電話號碼（例如：0912345678 或 02-12345678），不可包含英文字母。",
        }
        widgets = {
            "account": forms.TextInput(attrs={"autocomplete": "username"}),
            "phone": forms.TelInput(
                attrs={
                    "autocomplete": "tel",
                    "placeholder": "請輸入聯絡電話（例如：0912345678）",
                    "pattern": r"(\+?886-?|0)(9[0-9]{2}-?[0-9]{3}-?[0-9]{3}|9[0-9]{8}|[2-8][0-9]{0,2}-?[0-9]{6,8})",
                    "title": "請輸入有效的電話號碼（例如：0912345678 或 02-12345678），不可包含英文字母",
                }
            ),
        }

    def clean_account(self):
        account = self.cleaned_data["account"].strip()
        if User.objects.filter(account=account).exists():
            raise ValidationError("這個帳號已經註冊過了。")
        return account

    def clean_phone(self):
        return validate_phone_number(self.cleaned_data.get("phone", ""))

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
                    name=cleaned_data.get("name", ""),
                    group_name=cleaned_data.get("group_name", ""),
                )
                validate_password(password1, candidate)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
