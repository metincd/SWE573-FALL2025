from django.db.models import Q
from django.utils import timezone
from django.db import connection
from rest_framework import viewsets, permissions, filters, generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes

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
    ThankYouNote,
    Review,
    ReviewHelpfulVote,
    UserRating,
    Report,
    ModerationAction,
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
    ThankYouNoteSerializer,
    ReviewSerializer,
    UserRatingSerializer,
    ReportSerializer,
    ModerationActionSerializer,
    UserRegistrationSerializer,
)
from django.contrib.contenttypes.models import ContentType


@api_view(["GET"])
def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        # Database connectivity check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return Response(
            {
                "status": "healthy",
                "database": "connected",
                "timestamp": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, "owner", None)
        return owner == request.user


class IsModeratorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]
    
    @action(detail=False, methods=["get"])
    def popular(self, request):
        """Get popular tags ordered by service count"""
        from django.db.models import Count
        popular_tags = Tag.objects.annotate(
            service_count=Count('services')
        ).filter(service_count__gt=0).order_by('-service_count')[:20]
        serializer = self.get_serializer(popular_tags, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create tag with optional Wikidata integration"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wikidata_id = serializer.validated_data.get('wikidata_id')
        if wikidata_id:
            if not wikidata_id.startswith('Q') or not wikidata_id[1:].isdigit():
                return Response(
                    {"wikidata_id": "Invalid Wikidata ID format. Should be like Q12345"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not serializer.validated_data.get('wikidata_url'):
                serializer.validated_data['wikidata_url'] = f"https://www.wikidata.org/wiki/{wikidata_id}"
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
        owner = self.request.query_params.get("owner")
        
        # Geo filtering (lat/lng/radius_km)
        lat = self.request.query_params.get("lat")
        lng = self.request.query_params.get("lng")
        radius_km = self.request.query_params.get("radius_km")
        
        if service_type:
            qs = qs.filter(service_type=service_type)
        if status:
            qs = qs.filter(status=status)
        if tag:
            qs = qs.filter(Q(tags__slug=tag) | Q(tags__name__iexact=tag))
        if owner:
            try:
                qs = qs.filter(owner_id=int(owner))
            except (ValueError, TypeError):
                pass
        
        # Geo filter: basit bounding box yaklaşımı
        if lat and lng and radius_km:
            try:
                center_lat = float(lat)
                center_lng = float(lng)
                radius = float(radius_km)
                
                # Basit yaklaşım: 1 derece ≈ 111 km
                lat_delta = radius / 111.0
                lng_delta = radius / (111.0 * abs(center_lat / 90.0) + 0.001)  # Latitude'e göre adjust
                
                min_lat = center_lat - lat_delta
                max_lat = center_lat + lat_delta
                min_lng = center_lng - lng_delta
                max_lng = center_lng + lng_delta
                
                qs = qs.filter(
                    latitude__gte=min_lat,
                    latitude__lte=max_lat,
                    longitude__gte=min_lng,
                    longitude__lte=max_lng,
                )
            except (ValueError, TypeError):
                # Geçersiz değerler, geo filter uygulanmaz
                pass
        
        return qs

    def perform_create(self, serializer):
        service = serializer.save(owner=self.request.user)
        from .models import Thread
        if not service.discussion_thread:
            discussion_thread = Thread.objects.create(
                title=f"Discussion: {service.title}",
                author=self.request.user,
                related_service=service,
                status="open",
            )
            service.discussion_thread = discussion_thread
            service.save(update_fields=["discussion_thread"])


class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = (
            ServiceRequest.objects
            .select_related("service", "requester", "service__owner", "conversation")
            .prefetch_related("service__tags")
            .filter(Q(requester=user) | Q(service__owner=user))
        )
        # Filter by conversation if provided
        conversation_id = self.request.query_params.get("conversation")
        if conversation_id:
            try:
                qs = qs.filter(conversation_id=int(conversation_id))
            except (ValueError, TypeError):
                pass
        return qs.order_by("-created_at")
    
    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_object(self):
        """Override to ensure service.owner is loaded"""
        obj = super().get_object()
        # Ensure service and owner are loaded
        if hasattr(obj, 'service'):
            if not hasattr(obj.service, 'owner') or obj.service.owner is None:
                obj.service.refresh_from_db(fields=['owner'])
        return obj

    def perform_create(self, serializer):
        user = self.request.user
        service = serializer.validated_data.get('service')
        
        # Check if user already has a request for this service
        existing_request = ServiceRequest.objects.filter(
            requester=user,
            service=service
        ).first()
        
        if existing_request:
            raise ValidationError({
                'service': f'You already have a {existing_request.status} request for this service.'
            })
        
        # Check if user is trying to request their own service
        if service.owner == user:
            raise ValidationError({
                'service': 'You cannot request your own service.'
            })
        
        # Create ServiceRequest
        service_request = serializer.save(requester=user)
        
        # Create private conversation between requester and owner
        from .models import Conversation
        conversation = Conversation.objects.create(
            title=f"Chat: {service.title}",
            related_service=service,
        )
        conversation.participants.add(user, service.owner)
        service_request.conversation = conversation
        service_request.save(update_fields=["conversation"])

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        """Set status - for accept/reject (owner only) and cancel (requester only)"""
        sr = self.get_object()
        new_status = request.data.get("status")
        allowed = {"pending", "accepted", "rejected", "cancelled"}
        if new_status not in allowed:
            return Response({"detail": "Invalid status."}, status=400)
        user = request.user
        
        # Get service owner (should be loaded via select_related)
        service_owner_id = sr.service.owner_id if hasattr(sr.service, 'owner_id') else sr.service.owner.id
        
        if new_status == "cancelled" and sr.requester != user:
            return Response({"detail": "Only the requester can cancel this request."}, status=403)
        if new_status in {"accepted", "rejected"} and service_owner_id != user.id:
            return Response({
                "detail": f"Only the service owner can perform this action."
            }, status=403)
        
        sr.status = new_status
        # Service owner yanıt verdiğinde responded_at'i güncelle
        if new_status in {"accepted", "rejected"} and service_owner_id == user.id:
            sr.responded_at = timezone.now()
        
        sr.save(update_fields=["status", "responded_at", "updated_at"])
        return Response(ServiceRequestSerializer(sr).data)
    
    @action(detail=True, methods=["post"])
    def approve_start(self, request, pk=None):
        """Approve to start service - both parties must approve"""
        sr = self.get_object()
        user = request.user
        service_owner_id = sr.service.owner_id if hasattr(sr.service, 'owner_id') else sr.service.owner.id
        
        # Check if user is part of this request
        if user.id != service_owner_id and user.id != sr.requester.id:
            return Response({"detail": "You are not part of this service request."}, status=403)
        
        # Check if request is accepted
        if sr.status != "accepted":
            return Response({"detail": "Service request must be accepted first."}, status=400)
        
        # Set approval based on user role
        if user.id == service_owner_id:
            sr.owner_approved = True
        elif user.id == sr.requester.id:
            sr.requester_approved = True
        
        # If both approved, set status to in_progress
        if sr.owner_approved and sr.requester_approved:
            sr.status = "in_progress"
        
        sr.save()
        return Response(ServiceRequestSerializer(sr).data)
    
    @action(detail=True, methods=["post"])
    def update_hours(self, request, pk=None):
        """Update actual hours worked - can be called by either party"""
        sr = self.get_object()
        user = request.user
        service_owner_id = sr.service.owner_id if hasattr(sr.service, 'owner_id') else sr.service.owner.id
        
        # Check if user is part of this request
        if user.id != service_owner_id and user.id != sr.requester.id:
            return Response({"detail": "You are not part of this service request."}, status=403)
        
        # Check if service is in progress or completed
        if sr.status not in ["in_progress", "completed"]:
            return Response({"detail": "Service must be in progress or completed to update hours."}, status=400)
        
        actual_hours = request.data.get("actual_hours")
        if actual_hours is None:
            return Response({"detail": "actual_hours is required."}, status=400)
        
        try:
            from decimal import Decimal
            actual_hours = Decimal(str(actual_hours))
            if actual_hours < 0:
                return Response({"detail": "Hours cannot be negative."}, status=400)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid hours value."}, status=400)
        
        # Reset approvals when hours are updated
        sr.actual_hours = actual_hours
        sr.actual_hours_owner_approved = False
        sr.actual_hours_requester_approved = False
        
        sr.save()
        return Response(ServiceRequestSerializer(sr).data)
    
    @action(detail=True, methods=["post"])
    def approve_hours(self, request, pk=None):
        """Approve actual hours - both parties must approve"""
        sr = self.get_object()
        user = request.user
        service_owner_id = sr.service.owner_id if hasattr(sr.service, 'owner_id') else sr.service.owner.id
        
        # Check if user is part of this request
        if user.id != service_owner_id and user.id != sr.requester.id:
            return Response({"detail": "You are not part of this service request."}, status=403)
        
        # Check if actual hours is set
        if not sr.actual_hours:
            return Response({"detail": "Actual hours must be set first."}, status=400)
        
        # Set approval based on user role
        if user.id == service_owner_id:
            sr.actual_hours_owner_approved = True
        elif user.id == sr.requester.id:
            sr.actual_hours_requester_approved = True
        
        sr.save()
        return Response(ServiceRequestSerializer(sr).data)
    
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark service as completed - both parties must approve"""
        sr = self.get_object()
        user = request.user
        service_owner_id = sr.service.owner_id if hasattr(sr.service, 'owner_id') else sr.service.owner.id
        
        # Check if user is part of this request
        if user.id != service_owner_id and user.id != sr.requester.id:
            return Response({"detail": "You are not part of this service request."}, status=403)
        
        # Check if service is in progress
        if sr.status != "in_progress":
            return Response({"detail": "Service must be in progress to complete."}, status=400)
        
        # Use actual_hours if set and approved, otherwise use estimated_hours
        from decimal import Decimal
        if sr.actual_hours and sr.actual_hours_owner_approved and sr.actual_hours_requester_approved:
            service_hours = sr.actual_hours
        else:
            service_hours = Decimal(str(sr.service.estimated_hours or 0))
        
        if service_hours <= 0:
            return Response({"detail": "Service hours must be greater than 0."}, status=400)
        
        # Mark as completed (both parties need to call this)
        # For simplicity, we'll mark it as completed when either party calls it
        # In a more complex system, you might want separate completion flags
        sr.status = "completed"
        sr.save()
        

        service = sr.service
        active_requests = service.requests.exclude(status__in=['completed', 'rejected', 'cancelled']).exists()
        if not active_requests:
            service.status = "completed"
            service.save(update_fields=['status'])
        
        requester_account, _ = TimeAccount.objects.get_or_create(user=sr.requester)
        owner_account, _ = TimeAccount.objects.get_or_create(user=sr.service.owner)
        
        if requester_account.balance >= service_hours:
            requester_account.balance -= service_hours
            requester_account.total_spent += service_hours
            requester_account.save()
            
            owner_account.balance += service_hours
            owner_account.total_earned += service_hours
            owner_account.save()
            
            TimeTransaction.objects.create(
                account=requester_account,
                transaction_type="debit",
                amount=service_hours,
                status="completed",
                description=f"Payment for service: {sr.service.title}",
                related_service=sr.service,
                processed_by=user,
            )
            TimeTransaction.objects.create(
                account=owner_account,
                transaction_type="credit",
                amount=service_hours,
                status="completed",
                description=f"Earned from service: {sr.service.title}",
                related_service=sr.service,
                processed_by=user,
            )
        else:
            return Response(
                {"detail": f"Requester does not have enough balance. Required: {service_hours}h, Available: {requester_account.balance}h"},
                status=400
            )
        
        return Response(ServiceRequestSerializer(sr).data)


class MeView(generics.RetrieveUpdateAPIView):
    """Authenticated user's own profile"""

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_serializer_context(self):
        """Add request to serializer context for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        """Handle file upload for avatar"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        data = {
            'display_name': request.data.get('display_name', ''),
            'bio': request.data.get('bio', ''),
        }
        
        if 'avatar' in request.FILES:
            data['avatar'] = request.FILES['avatar']
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        self.perform_update(serializer)
        
        return Response(serializer.data)


class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to user profiles.
    Used to show other users' public profiles in chats and request lists.
    """

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Profile.objects.select_related("user").all()
    
    def get_serializer_context(self):
        """Add request to serializer context for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    """User registration endpoint - public access"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Create profile for the user
        Profile.objects.get_or_create(user=user)
        # Create time account with default 3 hours balance
        TimeAccount.objects.get_or_create(
            user=user,
            defaults={"balance": 3.00},
        )
        return Response(
            {"message": "User created successfully", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

    def perform_create(self, serializer):
        service_request = serializer.validated_data["service_request"]
        user = self.request.user
        # Sadece requester veya service owner session oluşturabilir
        if service_request.requester != user and service_request.service.owner != user:
            raise PermissionDenied("Only the requester or service owner can create sessions.")
        serializer.save()


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
        session = serializer.validated_data["session"]
        user = self.request.user
        # Sadece requester veya service owner completion oluşturabilir
        if (
            session.service_request.requester != user
            and session.service_request.service.owner != user
        ):
            raise PermissionDenied(
                "Only the requester or service owner can create completions."
            )
        serializer.save(marked_by=user)


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Conversation.objects
            .select_related("related_service")
            .prefetch_related("participants", "messages")
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

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Notifications cannot be created via API. They are system-generated."},
            status=405
        )

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


class ThankYouNoteViewSet(viewsets.ModelViewSet):
    serializer_class = ThankYouNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = (
            ThankYouNote.objects.select_related("from_user", "to_user", "related_service", "related_session")
            .filter(Q(from_user=user) | Q(to_user=user))
        )
        received = self.request.query_params.get("received")
        if received is not None:
            if received.lower() == "true":
                qs = qs.filter(to_user=user)
            else:
                qs = qs.filter(from_user=user)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Sadece gönderen kendi notunu güncelleyebilir
        if instance.from_user != request.user:
            return Response({"detail": "You can only edit notes you sent."}, status=403)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Sadece gönderen veya alan notu silebilir
        if instance.from_user != request.user and instance.to_user != request.user:
            return Response({"detail": "You can only delete notes you sent or received."}, status=403)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        note = self.get_object()
        if note.to_user != request.user:
            return Response({"detail": "You can only mark notes you received as read."}, status=403)
        note.mark_as_read()
        return Response(ThankYouNoteSerializer(note).data)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "content"]
    ordering_fields = ["created_at", "rating", "helpful_count"]
    ordering = ["-created_at"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        show_all = self.request.query_params.get("show_all", "false").lower() == "true"
        
        if show_all and user.is_authenticated:
            # Kullanıcı kendi review'larını görmek isterse published olmasa bile göster
            qs = Review.objects.select_related(
                "reviewer", "reviewee", "related_service", "related_session", "related_completion"
            ).filter(reviewer=user)
        else:
            # Varsayılan: sadece published review'lar
            qs = Review.objects.select_related(
                "reviewer", "reviewee", "related_service", "related_session", "related_completion"
            ).filter(is_published=True)
        
        reviewer = self.request.query_params.get("reviewer")
        reviewee = self.request.query_params.get("reviewee")
        review_type = self.request.query_params.get("review_type")
        rating = self.request.query_params.get("rating")
        related_service = self.request.query_params.get("service")
        
        if reviewer:
            qs = qs.filter(reviewer_id=reviewer)
        if reviewee:
            qs = qs.filter(reviewee_id=reviewee)
        if review_type:
            qs = qs.filter(review_type=review_type)
        if rating:
            qs = qs.filter(rating=rating)
        if related_service:
            qs = qs.filter(related_service_id=related_service)
        return qs

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    def get_object(self):
        obj = super().get_object()
        # Kullanıcı kendi review'ını veya published bir review'ı görebilir
        if not obj.is_published and obj.reviewer != self.request.user:
            raise PermissionDenied("You can only view published reviews or your own reviews.")
        return obj

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Sadece reviewer kendi review'ını güncelleyebilir
        if instance.reviewer != request.user:
            return Response({"detail": "You can only edit your own reviews."}, status=403)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Sadece reviewer kendi review'ını silebilir
        if instance.reviewer != request.user:
            return Response({"detail": "You can only delete your own reviews."}, status=403)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def helpful(self, request, pk=None):
        review = self.get_object()
        created = review.mark_helpful(request.user)
        if created:
            return Response({"detail": "Review marked as helpful"}, status=201)
        return Response({"detail": "Review already marked as helpful"})

    @action(detail=True, methods=["post"])
    def unhelpful(self, request, pk=None):
        review = self.get_object()
        removed = review.unmark_helpful(request.user)
        if removed:
            return Response({"detail": "Helpful mark removed"})
        return Response({"detail": "Review was not marked as helpful"})


class UserRatingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserRatingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["overall_rating", "overall_review_count"]
    ordering = ["-overall_rating"]

    def get_queryset(self):
        qs = UserRating.objects.select_related("user").all()
        user_id = self.request.query_params.get("user")
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Moderator/admin tüm report'ları görebilir
            qs = Report.objects.select_related("reporter", "content_type").all()
        else:
            # Normal kullanıcı sadece kendi report'larını görebilir
            qs = Report.objects.select_related("reporter", "content_type").filter(reporter=user)
        
        status = self.request.query_params.get("status")
        reason = self.request.query_params.get("reason")
        if status:
            qs = qs.filter(status=status)
        if reason:
            qs = qs.filter(reason=reason)
        return qs

    def perform_create(self, serializer):
        # Reporter'ı otomatik ata ve reporter_ip'yi kaydet
        serializer.save(
            reporter=self.request.user,
            reporter_ip=self.get_client_ip()
        )

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["is_moderator"] = (
            self.request.user.is_staff or self.request.user.is_superuser
        )
        return context

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Sadece moderator/admin report'u güncelleyebilir
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Only moderators can update reports."}, status=403)
        # Status'u manuel olarak güncelle
        status = request.data.get("status")
        if status:
            instance.status = status
            if status in ["resolved", "dismissed"] and not instance.resolved_at:
                instance.resolved_at = timezone.now()
            instance.save()
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        report = self.get_object()
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Only moderators can resolve reports."}, status=403)
        report.resolve(resolved_by=request.user)
        return Response(ReportSerializer(report).data)

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        report = self.get_object()
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Only moderators can dismiss reports."}, status=403)
        report.dismiss(dismissed_by=request.user)
        return Response(ReportSerializer(report).data)


class ModerationActionViewSet(viewsets.ModelViewSet):
    serializer_class = ModerationActionSerializer
    permission_classes = [IsModeratorOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "severity"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = (
            ModerationAction.objects.select_related(
                "moderator", "affected_user", "report"
            ).all()
        )
        action_type = self.request.query_params.get("action")
        severity = self.request.query_params.get("severity")
        affected_user = self.request.query_params.get("affected_user")
        is_reversed = self.request.query_params.get("is_reversed")
        if action_type:
            qs = qs.filter(action=action_type)
        if severity:
            qs = qs.filter(severity=severity)
        if affected_user:
            qs = qs.filter(affected_user_id=affected_user)
        if is_reversed is not None:
            qs = qs.filter(is_reversed=is_reversed.lower() == "true")
        return qs

    def perform_create(self, serializer):
        serializer.save(moderator=self.request.user)

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        action_obj = self.get_object()
        reason = request.data.get("reason", "")
        action_obj.reverse(reversed_by=request.user, reason=reason)
        return Response(ModerationActionSerializer(action_obj).data)
