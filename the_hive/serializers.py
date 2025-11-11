from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
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
from django.contrib.contenttypes.models import ContentType


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that uses email instead of username"""
    username_field = 'email'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove 'email' field and add 'username' field that accepts email
        if 'email' in self.fields:
            del self.fields['email']
        self.fields['username'] = serializers.EmailField()
        self.fields['username'].label = 'Email'

    def validate(self, attrs):
        # Convert 'username' to 'email' for parent class validation
        if 'username' in attrs:
            attrs['email'] = attrs.pop('username')
        return super().validate(attrs)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name", "date_joined"]
        read_only_fields = ["id", "email", "date_joined", "full_name"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password", "password2", "first_name", "last_name"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "display_name",
            "bio",
            "avatar_url",
            "latitude",
            "longitude",
            "preferred_languages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "description", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


class ServiceSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    tags = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Tag.objects.all(), required=False
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "owner",
            "service_type",
            "title",
            "description",
            "tags",
            "latitude",
            "longitude",
            "status",
            "estimated_hours",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class ServiceRequestSerializer(serializers.ModelSerializer):
    requester = UserSerializer(read_only=True)
    # For write: accept service ID
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        source='service',
        write_only=True,
        required=True
    )
    # For read: use nested serializer but avoid circular dependency
    service = serializers.SerializerMethodField()
    
    def get_service(self, obj):
        """Return service details with owner - always called for read operations"""
        # Get service_id first (more reliable)
        service_id = getattr(obj, 'service_id', None)
        if not service_id:
            # Try to get from service object
            service_obj = getattr(obj, 'service', None)
            if service_obj and hasattr(service_obj, 'id'):
                service_id = service_obj.id
            else:
                return None
        
        # Always reload service with owner to ensure it's loaded
        from .models import Service
        try:
            service = Service.objects.select_related('owner').get(id=service_id)
        except Service.DoesNotExist:
            return None
        
        # Build owner info
        owner_info = None
        if service.owner:
            try:
                owner_info = {
                    'id': service.owner.id,
                    'username': service.owner.username,
                    'email': service.owner.email,
                    'full_name': getattr(service.owner, 'get_full_name', lambda: '')() or service.owner.username,
                }
            except Exception:
                owner_info = {
                    'id': service.owner.id if hasattr(service.owner, 'id') else None,
                    'username': getattr(service.owner, 'username', 'Unknown'),
                }
        
        return {
            'id': service.id,
            'title': service.title,
            'description': service.description,
            'service_type': service.service_type,
            'estimated_hours': service.estimated_hours,
            'status': service.status,
            'owner': owner_info,
        }

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "requester",
            "service",
            "service_id",
            "status",
            "message",
            "response_note",
            "created_at",
            "updated_at",
            "responded_at",
        ]
        read_only_fields = ["id", "requester", "service", "created_at", "updated_at", "responded_at"]


class ServiceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceSession
        fields = [
            "id",
            "service_request",
            "scheduled_start",
            "scheduled_end",
            "actual_start",
            "actual_end",
            "status",
            "notes",
            "actual_hours",
            "scheduled_hours",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "actual_hours", "scheduled_hours", "created_at", "updated_at"]


class CompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Completion
        fields = [
            "id",
            "session",
            "marked_by",
            "status",
            "completion_notes",
            "time_transferred",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "marked_by", "created_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "body",
            "is_read",
            "read_at",
            "is_recent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "sender", "is_read", "read_at", "is_recent", "created_at", "updated_at"]


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        source="participants",
        write_only=True,
        required=False,
    )
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "participants",
            "participant_ids",
            "related_service",
            "title",
            "is_archived",
            "last_message",
            "unread_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "participants", "last_message", "unread_count", "created_at", "updated_at"]

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.unread_count_for_user(request.user)
        return 0


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "thread",
            "author",
            "body",
            "status",
            "is_flagged",
            "is_recent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "is_recent", "created_at", "updated_at"]


class ThreadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Tag.objects.all(), required=False
    )
    post_count = serializers.IntegerField(read_only=True)
    last_post = PostSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Thread
        fields = [
            "id",
            "title",
            "author",
            "status",
            "is_flagged",
            "related_service",
            "tags",
            "views_count",
            "post_count",
            "last_post",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "views_count",
            "post_count",
            "last_post",
            "is_active",
            "created_at",
            "updated_at",
        ]


class TimeAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_positive_balance = serializers.BooleanField(read_only=True)
    participation_ratio = serializers.FloatField(read_only=True)

    class Meta:
        model = TimeAccount
        fields = [
            "id",
            "user",
            "balance",
            "total_earned",
            "total_spent",
            "is_positive_balance",
            "participation_ratio",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "balance",
            "total_earned",
            "total_spent",
            "is_positive_balance",
            "participation_ratio",
            "created_at",
            "updated_at",
        ]


class TimeTransactionSerializer(serializers.ModelSerializer):
    signed_amount = serializers.FloatField(read_only=True)

    class Meta:
        model = TimeTransaction
        fields = [
            "id",
            "account",
            "transaction_type",
            "amount",
            "signed_amount",
            "status",
            "description",
            "related_service",
            "related_session",
            "related_completion",
            "processed_by",
            "processed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "account",
            "signed_amount",
            "processed_by",
            "processed_at",
            "created_at",
            "updated_at",
        ]


class NotificationSerializer(serializers.ModelSerializer):
    is_unread = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_urgent = serializers.BooleanField(read_only=True)
    action_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "notification_type",
            "title",
            "message",
            "priority",
            "payload",
            "related_service",
            "related_conversation",
            "related_thread",
            "is_read",
            "read_at",
            "is_dismissed",
            "dismissed_at",
            "is_unread",
            "is_active",
            "is_expired",
            "is_urgent",
            "action_url",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "is_read",
            "read_at",
            "is_dismissed",
            "dismissed_at",
            "is_unread",
            "is_active",
            "is_expired",
            "is_urgent",
            "action_url",
            "created_at",
            "updated_at",
        ]

    def get_action_url(self, obj):
        return obj.get_action_url()


class ThankYouNoteSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    to_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="to_user",
        write_only=True,
        required=True,
    )
    is_unread = serializers.BooleanField(read_only=True)
    message_preview = serializers.CharField(read_only=True)

    class Meta:
        model = ThankYouNote
        fields = [
            "id",
            "from_user",
            "to_user",
            "to_user_id",
            "message",
            "message_preview",
            "status",
            "related_service",
            "related_session",
            "is_unread",
            "read_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "from_user",
            "to_user",
            "message_preview",
            "status",
            "is_unread",
            "read_at",
            "created_at",
            "updated_at",
        ]


class ReviewHelpfulVoteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ReviewHelpfulVote
        fields = ["id", "review", "user", "created_at"]
        read_only_fields = ["id", "user", "created_at"]


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)
    reviewee = UserSerializer(read_only=True)
    reviewee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="reviewee",
        write_only=True,
        required=True,
    )
    rating_display = serializers.CharField(read_only=True)
    is_recent = serializers.BooleanField(read_only=True)
    is_positive = serializers.BooleanField(read_only=True)
    is_negative = serializers.BooleanField(read_only=True)
    has_user_voted_helpful = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "reviewer",
            "reviewee",
            "reviewee_id",
            "review_type",
            "related_service",
            "related_session",
            "related_completion",
            "rating",
            "rating_display",
            "title",
            "content",
            "is_anonymous",
            "is_verified",
            "is_featured",
            "helpful_count",
            "is_published",
            "is_flagged",
            "is_recent",
            "is_positive",
            "is_negative",
            "has_user_voted_helpful",
            "created_at",
            "updated_at",
            "published_at",
        ]
        read_only_fields = [
            "id",
            "reviewer",
            "reviewee",
            "helpful_count",
            "rating_display",
            "is_recent",
            "is_positive",
            "is_negative",
            "has_user_voted_helpful",
            "is_verified",
            "is_featured",
            "is_published",
            "is_flagged",
            "created_at",
            "updated_at",
            "published_at",
        ]

    def get_has_user_voted_helpful(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ReviewHelpfulVote.objects.filter(
                review=obj, user=request.user
            ).exists()
        return False


class UserRatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    has_ratings = serializers.BooleanField(read_only=True)
    rating_level = serializers.CharField(read_only=True)
    is_highly_rated = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserRating
        fields = [
            "id",
            "user",
            "overall_rating",
            "overall_review_count",
            "provider_rating",
            "provider_review_count",
            "receiver_rating",
            "receiver_review_count",
            "service_quality_rating",
            "service_quality_review_count",
            "rating_distribution",
            "has_ratings",
            "rating_level",
            "is_highly_rated",
            "is_verified_reviewer",
            "last_reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "overall_rating",
            "overall_review_count",
            "provider_rating",
            "provider_review_count",
            "receiver_rating",
            "receiver_review_count",
            "service_quality_rating",
            "service_quality_review_count",
            "rating_distribution",
            "has_ratings",
            "rating_level",
            "is_highly_rated",
            "last_reviewed_at",
            "created_at",
            "updated_at",
        ]


class ReportSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    reported_content_preview = serializers.CharField(read_only=True)
    content_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "content_type",
            "object_id",
            "content_type_name",
            "reason",
            "description",
            "status",
            "reported_content_preview",
            "is_pending",
            "evidence_url",
            "created_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = [
            "id",
            "reporter",
            "reported_content_preview",
            "is_pending",
            "status",
            "created_at",
            "updated_at",
            "resolved_at",
        ]

    def get_content_type_name(self, obj):
        if obj.content_type:
            return f"{obj.content_type.app_label}.{obj.content_type.model}"
        return None

    def validate(self, attrs):
        # Content type validasyonu
        content_type = attrs.get("content_type")
        if content_type:
            allowed_models = [
                "service",
                "servicerequest",
                "thread",
                "post",
                "message",
                "review",
                "conversation",
            ]
            if content_type.model.lower() not in allowed_models:
                raise serializers.ValidationError(
                    {
                        "content_type": f"Reports can only be submitted for: {', '.join(allowed_models)}"
                    }
                )
        return attrs


class ModerationActionSerializer(serializers.ModelSerializer):
    moderator = UserSerializer(read_only=True)
    affected_user = UserSerializer(read_only=True)
    reversed_by = UserSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ModerationAction
        fields = [
            "id",
            "report",
            "moderator",
            "affected_user",
            "action",
            "severity",
            "notes",
            "duration_days",
            "expires_at",
            "is_reversed",
            "reversed_by",
            "reversed_at",
            "reversal_reason",
            "is_active",
            "is_expired",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "moderator",
            "is_active",
            "is_expired",
            "reversed_by",
            "reversed_at",
            "created_at",
            "updated_at",
        ]

