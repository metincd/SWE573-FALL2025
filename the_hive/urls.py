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
    ProfileViewSet,
    MeView,
    health_check,
    register,
    admin_stats,
    admin_ban_user,
    admin_suspend_user,
    admin_unban_user,
    admin_unsuspend_user,
    get_content_type,
)
from .geocoding import geocode_address

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
router.register(r"profiles", ProfileViewSet, basename="profile")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("register/", register, name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("geocode/", geocode_address, name="geocode-address"),
    path("admin/stats/", admin_stats, name="admin-stats"),
    path("admin/users/<int:user_id>/ban/", admin_ban_user, name="admin-ban-user"),
    path("admin/users/<int:user_id>/suspend/", admin_suspend_user, name="admin-suspend-user"),
    path("admin/users/<int:user_id>/unban/", admin_unban_user, name="admin-unban-user"),
    path("admin/users/<int:user_id>/unsuspend/", admin_unsuspend_user, name="admin-unsuspend-user"),
    path("contenttypes/get/", get_content_type, name="get-content-type"),
    path("", include(router.urls)),
]


