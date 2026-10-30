from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import ListView, UpdateView

from .forms import validate_phone_number
from .models import User


class ManagerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.account != "Manager":
            messages.error(request, "此頁面僅限管理帳號使用。")
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)


class ManagerDashboardView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = User
    template_name = "management/dashboard.html"
    context_object_name = "members"
    ordering = ("account",)

    def get_queryset(self):
        return User.objects.exclude(account="Manager").order_by("account")


class ManagedUserForm(forms.ModelForm):
    new_password = forms.CharField(
        label="重設密碼（選填）",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="留空即可保留原密碼。",
    )

    class Meta:
        model = User
        fields = ("account", "phone")
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

    def clean_phone(self):
        return validate_phone_number(self.cleaned_data.get("phone", ""))

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user


class ManagedUserUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = User
    form_class = ManagedUserForm
    template_name = "management/user_form.html"
    pk_url_kwarg = "user_id"
    success_url = reverse_lazy("management:dashboard")

    def get_queryset(self):
        return User.objects.exclude(account="Manager")

    def form_valid(self, form):
        messages.success(self.request, "使用者資料已更新。")
        return super().form_valid(form)


class ManagedUserDeleteView(LoginRequiredMixin, ManagerRequiredMixin, View):
    http_method_names = ["post"]

    @method_decorator(require_POST)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, user_id):
        member = get_object_or_404(User.objects.exclude(account="Manager"), pk=user_id)
        member.delete()
        messages.success(request, "使用者及其相關資料已刪除。")
        return redirect(reverse("management:dashboard"))
