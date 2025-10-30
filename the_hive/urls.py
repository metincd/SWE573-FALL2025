from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TagViewSet, ServiceViewSet, ServiceRequestViewSet, MeView

router = DefaultRouter()
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"service-requests", ServiceRequestViewSet, basename="service-request")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]


