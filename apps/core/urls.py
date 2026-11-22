from django.urls import path

from .views import (CompareView, FeedbackSubmitView, HomeView, LocationDetailView, LocationMapView,
                    LocationsView, PostageView, RemittanceFormView,
                    RemittanceView, TicketView, TrackingView, refresh_csrf_token)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("tracking/", TrackingView.as_view(), name="tracking"),
    path("postage/", PostageView.as_view(), name="postage"),
    path("postage/compare/", CompareView.as_view(), name="compare"),
    path("locations/", LocationsView.as_view(), name="locations"),
    path("locations/map/", LocationMapView.as_view(), name="map"),
    path("locations/detail/<int:place_id>/", LocationDetailView.as_view(), name="location_detail"),
    path("remittance/", RemittanceView.as_view(), name="remittance"),
    path("remittance/form/", RemittanceFormView.as_view(), name="remittance_form"),
    path("remittance/ticket/", TicketView.as_view(), name="ticket"),
    path("feedback/", FeedbackSubmitView.as_view(), name="feedback_submit"),
    path("csrf-token/", refresh_csrf_token, name="csrf_token"),
]
