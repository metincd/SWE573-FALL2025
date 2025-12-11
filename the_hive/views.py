from django.db.models import Q, Count
from django.utils import timezone
from django.db import connection
from rest_framework import viewsets, permissions, filters, generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes

from .models import (
    User,
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
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def get_content_type(request):
    """Get ContentType ID for a given app_label and model"""
    app_label = request.query_params.get("app_label", "the_hive")
    model = request.query_params.get("model")
    
    if not model:
        return Response({"detail": "model parameter is required."}, status=400)
    
    try:
        content_type = ContentType.objects.get(app_label=app_label, model=model.lower())
        return Response({
            "id": content_type.id,
            "app_label": content_type.app_label,
            "model": content_type.model
        })
    except ContentType.DoesNotExist:
        return Response({"detail": f"ContentType not found for {app_label}.{model}"}, status=404)


@api_view(["GET"])
def health_check_old(request):
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
            Service.objects.select_related("owner", "owner__profile")
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
        user = self.request.user
        profile = user.profile
        
        if profile.is_banned:
            if profile.ban_expires_at and timezone.now() > profile.ban_expires_at:
                profile.is_banned = False
                profile.ban_reason = ""
                profile.ban_expires_at = None
                profile.save()
            else:
                raise ValidationError({
                    'detail': f'Your account is banned. Reason: {profile.ban_reason or "No reason provided"}.'
                })
        
        if profile.is_suspended:
            if profile.suspension_expires_at and timezone.now() > profile.suspension_expires_at:
                profile.is_suspended = False
                profile.suspension_reason = ""
                profile.suspension_expires_at = None
                profile.save()
            else:
                raise ValidationError({
                    'detail': f'Your account is suspended. Reason: {profile.suspension_reason or "No reason provided"}.'
                })
        
        service = serializer.save(owner=user)
        from .models import Thread
        if not service.discussion_thread:
            discussion_thread = Thread.objects.create(
                title=f"Discussion: {service.title}",
                author=user,
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
        
        if sr.service.service_type == "need":
            payer_account = owner_account
            receiver_account = requester_account
            payer_name = "Service owner"
            receiver_name = "Requester"
        else:
            payer_account = requester_account
            receiver_account = owner_account
            payer_name = "Requester"
            receiver_name = "Service owner"
        
        if payer_account.balance >= service_hours:
            payer_account.balance -= service_hours
            payer_account.total_spent += service_hours
            payer_account.save()
            
            receiver_account.balance += service_hours
            receiver_account.total_earned += service_hours
            receiver_account.save()
            
            TimeTransaction.objects.create(
                account=payer_account,
                transaction_type="debit",
                amount=service_hours,
                status="completed",
                description=f"Payment for service: {sr.service.title}",
                related_service=sr.service,
                processed_by=user,
            )
            TimeTransaction.objects.create(
                account=receiver_account,
                transaction_type="credit",
                amount=service_hours,
                status="completed",
                description=f"Earned from service: {sr.service.title}",
                related_service=sr.service,
                processed_by=user,
            )
        else:
            return Response(
                {"detail": f"{payer_name} does not have enough balance. Required: {service_hours}h, Available: {payer_account.balance}h"},
                status=400
            )
        
        return Response(ServiceRequestSerializer(sr).data)


class MeView(generics.RetrieveUpdateAPIView):
    """Authenticated user's own profile"""

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.select_related("user").get_or_create(user=self.request.user)
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
    lookup_field = 'user_id'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Profile.objects.select_related("user").all()
    
    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        user_id = self.kwargs[lookup_url_kwarg]
        try:
            profile = Profile.objects.select_related("user").get(user_id=user_id)
            self.check_object_permissions(self.request, profile)
            return profile
        except Profile.DoesNotExist:
            from django.http import Http404
            raise Http404("Profile not found for this user")
    
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
        profile, _ = Profile.objects.get_or_create(user=user)
        
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if latitude and longitude:
            try:
                profile.latitude = float(latitude)
                profile.longitude = float(longitude)
                profile.save()
            except (ValueError, TypeError):
                pass
        
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

    @action(detail=False, methods=["post"])
    def admin_message(self, request):
        """Admin can send a message to any user"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Only staff members can send admin messages."}, status=403)
        
        target_user_id = request.data.get("target_user_id")
        message_body = request.data.get("message")
        
        if not target_user_id or not message_body:
            return Response({"detail": "target_user_id and message are required."}, status=400)
        
        try:
            target_user = User.objects.get(id=target_user_id)
            admin_user = request.user
            
            conversation, created = Conversation.objects.get_or_create(
                title=f"Admin Message to {target_user.email}",
                defaults={}
            )
            conversation.participants.add(admin_user, target_user)
            
            message = Message.objects.create(
                conversation=conversation,
                sender=admin_user,
                body=message_body,
            )
            
            return Response({
                "message": "Admin message sent successfully.",
                "conversation_id": conversation.id,
                "message_id": message.id
            })
        except User.DoesNotExist:
            return Response({"detail": "Target user not found."}, status=404)


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
        user = self.request.user
        profile = user.profile
        
        if profile.is_banned:
            if profile.ban_expires_at and timezone.now() > profile.ban_expires_at:
                profile.is_banned = False
                profile.ban_reason = ""
                profile.ban_expires_at = None
                profile.save()
            else:
                raise ValidationError({
                    'detail': f'Your account is banned. Reason: {profile.ban_reason or "No reason provided"}.'
                })
        
        if profile.is_suspended:
            if profile.suspension_expires_at and timezone.now() > profile.suspension_expires_at:
                profile.is_suspended = False
                profile.suspension_reason = ""
                profile.suspension_expires_at = None
                profile.save()
            else:
                raise ValidationError({
                    'detail': f'Your account is suspended. Reason: {profile.suspension_reason or "No reason provided"}.'
                })
        
        conversation = serializer.validated_data["conversation"]
        if user not in conversation.participants.all():
            return Response(
                {"detail": "You are not a participant in this conversation."}, status=403
            )
        serializer.save(sender=user)

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
            Thread.objects.select_related("author", "author__profile", "related_service")
            .prefetch_related("tags", "posts", "posts__author", "posts__author__profile")
            .all()
        )
        status = self.request.query_params.get("status")
        is_flagged = self.request.query_params.get("flagged")
        tag = self.request.query_params.get("tag")
        service = self.request.query_params.get("service")
        forum_only = self.request.query_params.get("forum_only")
        if status:
            qs = qs.filter(status=status)
        if is_flagged is not None:
            qs = qs.filter(is_flagged=is_flagged.lower() == "true")
        if tag:
            qs = qs.filter(Q(tags__slug=tag) | Q(tags__name__iexact=tag))
        if service:
            qs = qs.filter(related_service_id=service)
        if forum_only and forum_only.lower() == "true":
            qs = qs.filter(related_service__isnull=True)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        profile = user.profile
        
        if profile.is_banned:
            if profile.ban_expires_at and timezone.now() > profile.ban_expires_at:
                profile.is_banned = False
                profile.ban_reason = ""
                profile.ban_expires_at = None
                profile.save()
            else:
                raise ValidationError({
                    'detail': f'Your account is banned. Reason: {profile.ban_reason or "No reason provided"}.'
                })
        
        if profile.is_suspended:
            if profile.suspension_expires_at and timezone.now() > profile.suspension_expires_at:
                profile.is_suspended = False
                profile.suspension_reason = ""
                profile.suspension_expires_at = None
                profile.save()
            else:
                raise ValidationError({
                    'detail': f'Your account is suspended. Reason: {profile.suspension_reason or "No reason provided"}.'
                })
        
        serializer.save(author=user)

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
        qs = Post.objects.select_related("author", "author__profile", "thread", "thread__author", "thread__author__profile").all()
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
        user = self.request.user
        profile = user.profile
        
        if profile.is_banned:
            if profile.ban_expires_at and timezone.now() > profile.ban_expires_at:
                profile.is_banned = False
                profile.ban_reason = ""
                profile.ban_expires_at = None
                profile.save()
            else:
                raise ValidationError({
                    'detail': f'Your account is banned. Reason: {profile.ban_reason or "No reason provided"}.'
                })
        
        if profile.is_suspended:
            if profile.suspension_expires_at and timezone.now() > profile.suspension_expires_at:
                profile.is_suspended = False
                profile.suspension_reason = ""
                profile.suspension_expires_at = None
                profile.save()
            else:
                raise ValidationError({
                    'detail': f'Your account is suspended. Reason: {profile.suspension_reason or "No reason provided"}.'
                })
        
        serializer.save(author=user)

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
        return TimeAccount.objects.select_related("user", "user__profile").filter(user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        time_account, _ = TimeAccount.objects.select_related("user", "user__profile").get_or_create(user=user)
        serializer = self.get_serializer(time_account)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        user = request.user
        time_account, _ = TimeAccount.objects.select_related("user", "user__profile").get_or_create(user=user)
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

    @action(detail=True, methods=["post"])
    def ban_user(self, request, pk=None):
        """Ban the user reported in this report"""
        report = self.get_object()
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Only moderators can ban users."}, status=403)
        
        reported_user = None
        if report.content_type.model == "user":
            reported_user = User.objects.get(id=report.object_id)
        elif report.content_type.model == "service":
            from .models import Service
            service = Service.objects.get(id=report.object_id)
            reported_user = service.owner
        elif report.content_type.model == "servicerequest":
            from .models import ServiceRequest
            service_request = ServiceRequest.objects.get(id=report.object_id)
            reported_user = service_request.requester
        elif report.content_type.model == "thread":
            from .models import Thread
            thread = Thread.objects.get(id=report.object_id)
            reported_user = thread.author
        elif report.content_type.model == "post":
            from .models import Post
            post = Post.objects.get(id=report.object_id)
            reported_user = post.author
        elif report.content_type.model == "message":
            from .models import Message
            message = Message.objects.get(id=report.object_id)
            reported_user = message.sender
        
        if not reported_user:
            return Response({"detail": "Could not identify the reported user."}, status=400)
        
        if reported_user.is_staff or reported_user.is_superuser:
            return Response({"detail": "Cannot ban staff members."}, status=400)
        
        reason = request.data.get("reason", f"Report #{report.id}: {report.reason}")
        expires_at = request.data.get("expires_at")
        
        profile = reported_user.profile
        profile.is_banned = True
        profile.ban_reason = reason
        if expires_at:
            from datetime import datetime
            profile.ban_expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        profile.save()
        
        ModerationAction.objects.create(
            report=report,
            moderator=request.user,
            affected_user=reported_user,
            action="user_banned",
            severity="high",
            notes=f"User banned due to report: {report.reason}. {report.description}"
        )
        
        report.resolve(resolved_by=request.user)
        
        from .models import Conversation, Message
        admin_user = request.user
        
        conv1, _ = Conversation.objects.get_or_create(
            title=f"Account Action: Ban",
            defaults={}
        )
        conv1.participants.add(admin_user, reported_user)
        Message.objects.create(
            conversation=conv1,
            sender=admin_user,
            body=f"Your account has been banned due to a report. Reason: {reason}. You will not be able to create services or send messages. If you believe this is an error, please contact support."
        )
        
        # Message to reporter
        conv2, _ = Conversation.objects.get_or_create(
            title=f"Report #{report.id} - Action Taken",
            defaults={}
        )
        conv2.participants.add(admin_user, report.reporter)
        Message.objects.create(
            conversation=conv2,
            sender=admin_user,
            body=f"Thank you for your report. We have reviewed it and taken action. The reported user has been banned. Report ID: #{report.id}"
        )
        
        return Response({
            "message": f"User {reported_user.email} has been banned.",
            "report": ReportSerializer(report).data
        })

    @action(detail=True, methods=["post"])
    def suspend_user(self, request, pk=None):
        """Suspend the user reported in this report"""
        report = self.get_object()
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Only moderators can suspend users."}, status=403)
        
        # Get the reported user
        reported_user = None
        if report.content_type.model == "user":
            reported_user = User.objects.get(id=report.object_id)
        elif report.content_type.model == "service":
            from .models import Service
            service = Service.objects.get(id=report.object_id)
            reported_user = service.owner
        elif report.content_type.model == "servicerequest":
            from .models import ServiceRequest
            service_request = ServiceRequest.objects.get(id=report.object_id)
            reported_user = service_request.requester
        elif report.content_type.model == "thread":
            from .models import Thread
            thread = Thread.objects.get(id=report.object_id)
            reported_user = thread.author
        elif report.content_type.model == "post":
            from .models import Post
            post = Post.objects.get(id=report.object_id)
            reported_user = post.author
        elif report.content_type.model == "message":
            from .models import Message
            message = Message.objects.get(id=report.object_id)
            reported_user = message.sender
        
        if not reported_user:
            return Response({"detail": "Could not identify the reported user."}, status=400)
        
        if reported_user.is_staff or reported_user.is_superuser:
            return Response({"detail": "Cannot suspend staff members."}, status=400)
        
        reason = request.data.get("reason", f"Report #{report.id}: {report.reason}")
        expires_at = request.data.get("expires_at")
        
        # Suspend the user
        profile = reported_user.profile
        profile.is_suspended = True
        profile.suspension_reason = reason
        if expires_at:
            from datetime import datetime
            profile.suspension_expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        profile.save()
        
        # Create moderation action
        ModerationAction.objects.create(
            report=report,
            moderator=request.user,
            affected_user=reported_user,
            action="user_suspended",
            severity="medium",
            notes=f"User suspended due to report: {report.reason}. {report.description}"
        )
        
        # Resolve the report
        report.resolve(resolved_by=request.user)
        
        # Send messages to both reporter and reported user
        from .models import Conversation, Message
        admin_user = request.user
        
        # Message to reported user
        conv1, _ = Conversation.objects.get_or_create(
            title=f"Account Action: Suspension",
            defaults={}
        )
        conv1.participants.add(admin_user, reported_user)
        Message.objects.create(
            conversation=conv1,
            sender=admin_user,
            body=f"Your account has been temporarily suspended due to a report. Reason: {reason}. You will not be able to create services or send messages during this period. If you believe this is an error, please contact support: metincemdogan@hotmail.com"
        )
        
        # Message to reporter
        conv2, _ = Conversation.objects.get_or_create(
            title=f"Report #{report.id} - Action Taken",
            defaults={}
        )
        conv2.participants.add(admin_user, report.reporter)
        Message.objects.create(
            conversation=conv2,
            sender=admin_user,
            body=f"Thank you for your report. We have reviewed it and taken action. The reported user has been suspended. Report ID: #{report.id}"
        )
        
        return Response({
            "message": f"User {reported_user.email} has been suspended.",
            "report": ReportSerializer(report).data
        })

    @action(detail=True, methods=["post"])
    def delete_content(self, request, pk=None):
        """Delete the reported content (service, post, thread, message)"""
        report = self.get_object()
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Only moderators can delete content."}, status=403)
        
        content_type_model = report.content_type.model
        object_id = report.object_id
        
        deleted_content_type = None
        deleted_content_id = None
        
        try:
            if content_type_model == "service":
                from .models import Service
                service = Service.objects.get(id=object_id)
                deleted_content_type = "service"
                deleted_content_id = service.id
                service.delete()
            elif content_type_model == "post":
                from .models import Post
                post = Post.objects.get(id=object_id)
                deleted_content_type = "post"
                deleted_content_id = post.id
                post.delete()
            elif content_type_model == "thread":
                from .models import Thread
                thread = Thread.objects.get(id=object_id)
                deleted_content_type = "thread"
                deleted_content_id = thread.id
                thread.delete()
            elif content_type_model == "message":
                from .models import Message
                message = Message.objects.get(id=object_id)
                deleted_content_type = "message"
                deleted_content_id = message.id
                message.delete()
            else:
                return Response({
                    "detail": f"Cannot delete content of type: {content_type_model}. Only service, post, thread, and message can be deleted."
                }, status=400)
        except Exception as e:
            return Response({
                "detail": f"Error deleting content: {str(e)}"
            }, status=400)
        
        # Create moderation action
        ModerationAction.objects.create(
            report=report,
            moderator=request.user,
            action="content_deleted",
            severity="high",
            notes=f"Deleted {deleted_content_type} (ID: {deleted_content_id}) due to report: {report.reason}. {report.description}"
        )
        
        report.resolve(resolved_by=request.user)
        
        from .models import Conversation, Message
        admin_user = request.user
        
        conv, _ = Conversation.objects.get_or_create(
            title=f"Report #{report.id} - Content Deleted",
            defaults={}
        )
        conv.participants.add(admin_user, report.reporter)
        Message.objects.create(
            conversation=conv,
            sender=admin_user,
            body=f"Thank you for your report. We have reviewed it and deleted the reported {deleted_content_type}. Report ID: #{report.id}"
        )
        
        return Response({
            "message": f"{deleted_content_type.capitalize()} (ID: {deleted_content_id}) has been deleted.",
            "report": ReportSerializer(report).data
        })


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


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def admin_stats(request):
    """Admin panel statistics endpoint"""
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({"detail": "Only staff members can access admin statistics."}, status=403)
    
    from datetime import timedelta
    from .models import Service, ServiceRequest, Report, User, Thread, Post, ModerationAction
    
    now = timezone.now()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    
    stats = {
        "services": {
            "total": Service.objects.count(),
            "active": Service.objects.filter(status="active").count(),
            "completed": Service.objects.filter(status="completed").count(),
            "inactive": Service.objects.filter(status="inactive").count(),
            "offers": Service.objects.filter(service_type="offer").count(),
            "needs": Service.objects.filter(service_type="need").count(),
            "created_last_7_days": Service.objects.filter(created_at__gte=last_7_days).count(),
            "created_last_30_days": Service.objects.filter(created_at__gte=last_30_days).count(),
        },
        "service_requests": {
            "total": ServiceRequest.objects.count(),
            "pending": ServiceRequest.objects.filter(status="pending").count(),
            "accepted": ServiceRequest.objects.filter(status="accepted").count(),
            "completed": ServiceRequest.objects.filter(status="completed").count(),
            "created_last_7_days": ServiceRequest.objects.filter(created_at__gte=last_7_days).count(),
        },
        "reports": {
            "total": Report.objects.count(),
            "pending": Report.objects.filter(status="pending").count(),
            "under_review": Report.objects.filter(status="under_review").count(),
            "resolved": Report.objects.filter(status="resolved").count(),
            "dismissed": Report.objects.filter(status="dismissed").count(),
            "by_reason": dict(Report.objects.values("reason").annotate(count=Count("id")).values_list("reason", "count")),
            "created_last_7_days": Report.objects.filter(created_at__gte=last_7_days).count(),
        },
        "users": {
            "total": User.objects.count(),
            "active": User.objects.filter(is_active=True).count(),
            "staff": User.objects.filter(is_staff=True).count(),
            "banned": User.objects.filter(profile__is_banned=True).count(),
            "suspended": User.objects.filter(profile__is_suspended=True).count(),
            "registered_last_7_days": User.objects.filter(date_joined__gte=last_7_days).count(),
            "registered_last_30_days": User.objects.filter(date_joined__gte=last_30_days).count(),
        },
        "forum": {
            "total_threads": Thread.objects.count(),
            "total_posts": Post.objects.count(),
            "forum_threads": Thread.objects.filter(related_service__isnull=True).count(),
            "service_discussions": Thread.objects.filter(related_service__isnull=False).count(),
            "threads_last_7_days": Thread.objects.filter(created_at__gte=last_7_days).count(),
            "posts_last_7_days": Post.objects.filter(created_at__gte=last_7_days).count(),
        },
        "moderation": {
            "total_actions": ModerationAction.objects.count(),
            "active_bans": User.objects.filter(profile__is_banned=True).count(),
            "active_suspensions": User.objects.filter(profile__is_suspended=True).count(),
            "actions_last_7_days": ModerationAction.objects.filter(created_at__gte=last_7_days).count(),
        }
    }
    
    return Response(stats)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def admin_ban_user(request, user_id):
    """Ban a user"""
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({"detail": "Only staff members can ban users."}, status=403)
    
    try:
        target_user = User.objects.get(id=user_id)
        if target_user.is_staff or target_user.is_superuser:
            return Response({"detail": "Cannot ban staff members."}, status=400)
        
        profile = target_user.profile
        profile.is_banned = True
        profile.ban_reason = request.data.get("reason", "")
        expires_at = request.data.get("expires_at")
        if expires_at:
            from datetime import datetime
            profile.ban_expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        profile.save()
        
        ModerationAction.objects.create(
            moderator=request.user,
            affected_user=target_user,
            action="user_banned",
            severity="high",
            notes=profile.ban_reason,
            expires_at=profile.ban_expires_at
        )
        
        return Response({"message": f"User {target_user.email} has been banned."})
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=404)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def admin_suspend_user(request, user_id):
    """Suspend a user"""
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({"detail": "Only staff members can suspend users."}, status=403)
    
    try:
        target_user = User.objects.get(id=user_id)
        if target_user.is_staff or target_user.is_superuser:
            return Response({"detail": "Cannot suspend staff members."}, status=400)
        
        profile = target_user.profile
        profile.is_suspended = True
        profile.suspension_reason = request.data.get("reason", "")
        expires_at = request.data.get("expires_at")
        if expires_at:
            from datetime import datetime
            profile.suspension_expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        profile.save()
        
        ModerationAction.objects.create(
            moderator=request.user,
            affected_user=target_user,
            action="user_suspended",
            severity="medium",
            notes=profile.suspension_reason,
            expires_at=profile.suspension_expires_at
        )
        
        return Response({"message": f"User {target_user.email} has been suspended."})
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=404)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def admin_unban_user(request, user_id):
    """Unban a user"""
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({"detail": "Only staff members can unban users."}, status=403)
    
    try:
        target_user = User.objects.get(id=user_id)
        profile = target_user.profile
        profile.is_banned = False
        profile.ban_reason = ""
        profile.ban_expires_at = None
        profile.save()
        
        return Response({"message": f"User {target_user.email} has been unbanned."})
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=404)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def admin_unsuspend_user(request, user_id):
    """Unsuspend a user"""
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({"detail": "Only staff members can unsuspend users."}, status=403)
    
    try:
        target_user = User.objects.get(id=user_id)
        profile = target_user.profile
        profile.is_suspended = False
        profile.suspension_reason = ""
        profile.suspension_expires_at = None
        profile.save()
        
        return Response({"message": f"User {target_user.email} has been unsuspended."})
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=404)
