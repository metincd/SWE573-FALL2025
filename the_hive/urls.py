from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TagViewSet,
    ServiceViewSet,
    ServiceRequestViewSet,
    ServiceSessionViewSet,
    CompletionViewSet,
    MeView,
)

router = DefaultRouter()
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"service-requests", ServiceRequestViewSet, basename="service-request")
router.register(r"sessions", ServiceSessionViewSet, basename="service-session")
router.register(r"completions", CompletionViewSet, basename="completion")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]


