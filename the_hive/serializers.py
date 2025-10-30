from rest_framework import serializers
from .models import User, Profile, Tag, Service, ServiceRequest


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


