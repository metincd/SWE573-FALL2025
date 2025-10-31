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
    TimeAccountViewSet,
    TimeTransactionViewSet,
    NotificationViewSet,
    ThankYouNoteViewSet,
    ReviewViewSet,
    UserRatingViewSet,
    ReportViewSet,
    ModerationActionViewSet,
    MeView,
    health_check,
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
router.register(r"time-accounts", TimeAccountViewSet, basename="time-account")
router.register(r"time-transactions", TimeTransactionViewSet, basename="time-transaction")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"thank-you-notes", ThankYouNoteViewSet, basename="thank-you-note")
router.register(r"reviews", ReviewViewSet, basename="review")
router.register(r"user-ratings", UserRatingViewSet, basename="user-rating")
router.register(r"reports", ReportViewSet, basename="report")
router.register(r"moderation-actions", ModerationActionViewSet, basename="moderation-action")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]


