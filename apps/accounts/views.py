from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import CreateView

from .forms import RegisterForm


@method_decorator([ensure_csrf_cookie, never_cache], name="dispatch")
class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        if self.request.user.account == "Manager":
            return reverse("management:dashboard")
        return super().get_success_url()


@method_decorator([ensure_csrf_cookie, never_cache], name="dispatch")
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = "/"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(
            self.request,
            self.object,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        messages.success(self.request, "註冊成功，已自動登入。")
        return response
