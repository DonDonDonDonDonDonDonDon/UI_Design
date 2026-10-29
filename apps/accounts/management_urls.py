from django.urls import path

from .management_views import (
    ManagedUserDeleteView,
    ManagedUserUpdateView,
    ManagerDashboardView,
)

app_name = "management"

urlpatterns = [
    path("", ManagerDashboardView.as_view(), name="dashboard"),
    path("users/<int:user_id>/edit/", ManagedUserUpdateView.as_view(), name="user_edit"),
    path("users/<int:user_id>/delete/", ManagedUserDeleteView.as_view(), name="user_delete"),
]
