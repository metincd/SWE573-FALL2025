from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, filters, generics
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    Profile,
    Tag,
    Service,
    ServiceRequest,
    ServiceSession,
    Completion,
    Conversation,
    Message,
    Thread,
    Post,
    TimeAccount,
    TimeTransaction,
    Notification,
)
from .serializers import (
    ProfileSerializer,
    TagSerializer,
    ServiceSerializer,
    ServiceRequestSerializer,
    ServiceSessionSerializer,
    CompletionSerializer,
    ConversationSerializer,
    MessageSerializer,
    ThreadSerializer,
    PostSerializer,
    TimeAccountSerializer,
    TimeTransactionSerializer,
    NotificationSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, "owner", None)
        return owner == request.user


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]


class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description", "tags__name", "tags__slug"]

    def get_queryset(self):
        qs = (
            Service.objects.select_related("owner")
            .prefetch_related("tags")
            .all()
        )
        service_type = self.request.query_params.get("type")
        status = self.request.query_params.get("status")
        tag = self.request.query_params.get("tag")
        if service_type:
            qs = qs.filter(service_type=service_type)
        if status:
            qs = qs.filter(status=status)
        if tag:
            qs = qs.filter(Q(tags__slug=tag) | Q(tags__name__iexact=tag))
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            ServiceRequest.objects.select_related("service", "requester", "service__owner")
            .filter(Q(requester=user) | Q(service__owner=user))
        )

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        sr = self.get_object()
        new_status = request.data.get("status")
        allowed = {"pending", "accepted", "rejected", "completed", "cancelled"}
        if new_status not in allowed:
            return Response({"detail": "Geçersiz durum."}, status=400)
        user = request.user
        if new_status == "cancelled" and sr.requester != user:
            return Response({"detail": "Bu işlemi sadece talep sahibi yapabilir."}, status=403)
        if new_status in {"accepted", "rejected", "completed"} and sr.service.owner != user:
            return Response({"detail": "Bu işlemi sadece servis sahibi yapabilir."}, status=403)
        sr.status = new_status
        sr.save(update_fields=["status", "updated_at"])
        return Response(ServiceRequestSerializer(sr).data)


class MeView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class ServiceSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            ServiceSession.objects.select_related(
                "service_request",
                "service_request__service",
                "service_request__requester",
                "service_request__service__owner",
            )
            .filter(
                Q(service_request__requester=user) | Q(service_request__service__owner=user)
            )
            .order_by("-scheduled_start")
        )


class CompletionViewSet(viewsets.ModelViewSet):
    serializer_class = CompletionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Completion.objects.select_related(
                "session",
                "marked_by",
                "session__service_request",
                "session__service_request__service",
            )
            .filter(
                Q(marked_by=user)
                | Q(session__service_request__service__owner=user)
                | Q(session__service_request__requester=user)
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(marked_by=self.request.user)


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Conversation.objects.prefetch_related("participants", "messages")
            .prefetch_related("related_service")
            .filter(participants=user)
            .order_by("-updated_at")
        )
        is_archived = self.request.query_params.get("archived")
        if is_archived is not None:
            qs = qs.filter(is_archived=is_archived.lower() == "true")
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        conversation = serializer.save()
        if self.request.user not in conversation.participants.all():
            conversation.participants.add(self.request.user)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        conv = self.get_object()
        conv.is_archived = True
        conv.save()
        return Response(ConversationSerializer(conv, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def unarchive(self, request, pk=None):
        conv = self.get_object()
        conv.is_archived = False
        conv.save()
        return Response(ConversationSerializer(conv, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        conv = self.get_object()
        conv.mark_as_read_for_user(request.user)
        return Response({"detail": "Conversation marked as read"})


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        conversation_id = self.request.query_params.get("conversation")
        qs = (
            Message.objects.select_related("sender", "conversation")
            .filter(conversation__participants=user)
            .order_by("-created_at")
        )
        if conversation_id:
            qs = qs.filter(conversation_id=conversation_id)
        return qs

    def perform_create(self, serializer):
        conversation = serializer.validated_data["conversation"]
        if self.request.user not in conversation.participants.all():
            return Response(
                {"detail": "You are not a participant in this conversation."}, status=403
            )
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        message = self.get_object()
        if message.conversation.participants.filter(id=request.user.id).exists():
            message.mark_as_read()
            return Response(MessageSerializer(message).data)
        return Response({"detail": "You are not a participant."}, status=403)


class ThreadViewSet(viewsets.ModelViewSet):
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title"]

    def get_queryset(self):
        qs = (
            Thread.objects.select_related("author", "related_service")
            .prefetch_related("tags", "posts")
            .all()
        )
        status = self.request.query_params.get("status")
        is_flagged = self.request.query_params.get("flagged")
        tag = self.request.query_params.get("tag")
        service = self.request.query_params.get("service")
        if status:
            qs = qs.filter(status=status)
        if is_flagged is not None:
            qs = qs.filter(is_flagged=is_flagged.lower() == "true")
        if tag:
            qs = qs.filter(Q(tags__slug=tag) | Q(tags__name__iexact=tag))
        if service:
            qs = qs.filter(related_service_id=service)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=["views_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def flag(self, request, pk=None):
        thread = self.get_object()
        reason = request.data.get("reason", "")
        thread.flag(user=request.user, reason=reason)
        return Response(ThreadSerializer(thread).data)

    @action(detail=True, methods=["post"])
    def unflag(self, request, pk=None):
        thread = self.get_object()
        if not request.user.is_staff:
            return Response({"detail": "Permission denied."}, status=403)
        thread.unflag()
        return Response(ThreadSerializer(thread).data)


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["body"]

    def get_queryset(self):
        qs = Post.objects.select_related("author", "thread", "thread__author").all()
        thread_id = self.request.query_params.get("thread")
        is_flagged = self.request.query_params.get("flagged")
        status = self.request.query_params.get("status")
        if thread_id:
            qs = qs.filter(thread_id=thread_id)
        if is_flagged is not None:
            qs = qs.filter(is_flagged=is_flagged.lower() == "true")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"])
    def flag(self, request, pk=None):
        post = self.get_object()
        reason = request.data.get("reason", "")
        post.flag(user=request.user, reason=reason)
        return Response(PostSerializer(post).data)

    @action(detail=True, methods=["post"])
    def unflag(self, request, pk=None):
        post = self.get_object()
        if not request.user.is_staff:
            return Response({"detail": "Permission denied."}, status=403)
        post.unflag()
        return Response(PostSerializer(post).data)


class TimeAccountViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TimeAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return TimeAccount.objects.filter(user=user)

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        time_account, _ = TimeAccount.objects.get_or_create(user=user)
        serializer = self.get_serializer(time_account)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        user = request.user
        time_account, _ = TimeAccount.objects.get_or_create(user=user)
        serializer = self.get_serializer(time_account)
        return Response([serializer.data])


class TimeTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TimeTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = (
            TimeTransaction.objects.select_related(
                "account", "related_service", "related_session", "related_completion", "processed_by"
            )
            .filter(account__user=user)
        )
        transaction_type = self.request.query_params.get("type")
        status = self.request.query_params.get("status")
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)
        if status:
            qs = qs.filter(status=status)
        return qs


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "priority"]
    ordering = ["-created_at"]
    http_method_names = ["get", "delete", "post"]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Notification.objects.select_related(
                "related_service", "related_conversation", "related_thread"
            )
            .filter(user=user)
        )
        is_read = self.request.query_params.get("is_read")
        notification_type = self.request.query_params.get("type")
        priority = self.request.query_params.get("priority")
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == "true")
        if notification_type:
            qs = qs.filter(notification_type=notification_type)
        if priority:
            qs = qs.filter(priority=priority)
        return qs

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response(NotificationSerializer(notification).data)

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        notification = self.get_object()
        notification.dismiss()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({"detail": f"{count} notifications marked as read"})

    @action(detail=False, methods=["delete"])
    def delete_expired(self, request):
        expired_count = self.get_queryset().filter(expires_at__lt=timezone.now()).count()
        self.get_queryset().filter(expires_at__lt=timezone.now()).delete()
        return Response({"detail": f"{expired_count} expired notifications deleted"})
