from django.db.models import Q
from rest_framework import viewsets, permissions, filters, generics
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Profile, Tag, Service, ServiceRequest
from .serializers import (
    ProfileSerializer,
    TagSerializer,
    ServiceSerializer,
    ServiceRequestSerializer,
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
