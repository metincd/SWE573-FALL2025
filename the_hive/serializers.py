from rest_framework import serializers
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
)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name", "date_joined"]
        read_only_fields = ["id", "email", "date_joined", "full_name"]


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

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "requester",
            "service",
            "status",
            "message",
            "response_note",
            "created_at",
            "updated_at",
            "responded_at",
        ]
        read_only_fields = ["id", "requester", "created_at", "updated_at", "responded_at"]


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
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "participants",
            "related_service",
            "title",
            "is_archived",
            "last_message",
            "unread_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_message", "unread_count", "created_at", "updated_at"]

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.unread_count_for_user(request.user)
        return 0

