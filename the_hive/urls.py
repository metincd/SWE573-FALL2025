from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TagViewSet,
    ServiceViewSet,
    ServiceRequestViewSet,
    ServiceSessionViewSet,
    CompletionViewSet,
    ConversationViewSet,
    MessageViewSet,
    ThreadViewSet,
    PostViewSet,
    MeView,
)

router = DefaultRouter()
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"service-requests", ServiceRequestViewSet, basename="service-request")
router.register(r"sessions", ServiceSessionViewSet, basename="service-session")
router.register(r"completions", CompletionViewSet, basename="completion")
router.register(r"conversations", ConversationViewSet, basename="conversation")
router.register(r"messages", MessageViewSet, basename="message")
router.register(r"threads", ThreadViewSet, basename="thread")
router.register(r"posts", PostViewSet, basename="post")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]


