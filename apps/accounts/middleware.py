from django.shortcuts import redirect
from django.urls import reverse


class ManagerAreaMiddleware:
    """Keep the Manager account inside its management-only area."""

    allowed_prefixes = ("/management/", "/accounts/logout/", "/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and request.user.account == "Manager"
            and not request.path_info.startswith(self.allowed_prefixes)
        ):
            return redirect(reverse("management:dashboard"))
        return self.get_response(request)
