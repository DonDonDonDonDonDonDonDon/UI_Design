from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from apps.accounts.views import LoginView, RegisterView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login-shortcut"),
    path("register/", RegisterView.as_view(), name="register-shortcut"),
    path("management/", include("apps.accounts.management_urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
