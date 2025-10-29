from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import (
    User, Profile, Tag, Service, ServiceRequest, 
    ServiceSession, Completion, TimeAccount, TimeTransaction
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_staff", "is_active", "date_joined")
    ordering = ("-date_joined",)
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )

    readonly_fields = ("date_joined",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "latitude", "longitude", "updated_at")
    search_fields = ("user__email", "display_name")
    list_filter = ("created_at", "updated_at")


# Services Admin

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "title", 
        "owner", 
        "service_type", 
        "status", 
        "estimated_hours",
        "created_at"
    )
    list_filter = ("service_type", "status", "created_at", "tags")
    search_fields = ("title", "description", "owner__email")
    filter_horizontal = ("tags",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("owner", "service_type", "title", "description")
        }),
        ("Details", {
            "fields": ("tags", "estimated_hours", "status")
        }),
        ("Location", {
            "fields": ("latitude", "longitude"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "requester",
        "service", 
        "status",
        "created_at",
        "responded_at"
    )
    list_filter = ("status", "created_at", "responded_at")
    search_fields = (
        "requester__email", 
        "service__title", 
        "message",
        "response_note"
    )
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("requester", "service", "status")
        }),
        ("Messages", {
            "fields": ("message", "response_note")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "responded_at"),
            "classes": ("collapse",)
        }),
    )


class ServiceSessionInline(admin.StackedInline):
    model = ServiceSession
    extra = 0
    readonly_fields = ("actual_hours", "scheduled_hours", "created_at", "updated_at")


@admin.register(ServiceSession)
class ServiceSessionAdmin(admin.ModelAdmin):
    list_display = (
        "service_request",
        "status",
        "scheduled_start",
        "scheduled_end",
        "actual_hours",
        "scheduled_hours"
    )
    list_filter = ("status", "scheduled_start", "created_at")
    search_fields = (
        "service_request__requester__email",
        "service_request__service__title",
        "notes"
    )
    readonly_fields = ("actual_hours", "scheduled_hours", "created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("service_request", "status")
        }),
        ("Scheduling", {
            "fields": ("scheduled_start", "scheduled_end", "scheduled_hours")
        }),
        ("Actual Time", {
            "fields": ("actual_start", "actual_end", "actual_hours")
        }),
        ("Notes", {
            "fields": ("notes",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Completion)
class CompletionAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "marked_by",
        "status",
        "time_transferred",
        "confirmed_at",
        "created_at"
    )
    list_filter = ("status", "time_transferred", "confirmed_at", "created_at")
    search_fields = (
        "session__service_request__service__title",
        "marked_by__email",
        "completion_notes"
    )
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("session", "marked_by", "status")
        }),
        ("Completion Details", {
            "fields": ("completion_notes", "time_transferred", "confirmed_at")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


class TimeTransactionInline(admin.TabularInline):
    model = TimeTransaction
    extra = 0
    readonly_fields = ("signed_amount", "created_at", "processed_at")
    fields = (
        "transaction_type", 
        "amount", 
        "signed_amount",
        "status", 
        "description", 
        "created_at"
    )


@admin.register(TimeAccount)
class TimeAccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "balance",
        "total_earned",
        "total_spent",
        "participation_ratio",
        "is_positive_balance",
        "updated_at"
    )
    list_filter = ("balance", "created_at", "updated_at")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    readonly_fields = (
        "participation_ratio", 
        "is_positive_balance",
        "created_at", 
        "updated_at"
    )
    inlines = [TimeTransactionInline]
    
    fieldsets = (
        (None, {
            "fields": ("user",)
        }),
        ("Balance Information", {
            "fields": (
                "balance", 
                "total_earned", 
                "total_spent",
                "participation_ratio",
                "is_positive_balance"
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(TimeTransaction)
class TimeTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "account",
        "transaction_type",
        "signed_amount",
        "status",
        "description",
        "created_at",
        "processed_at"
    )
    list_filter = (
        "transaction_type",
        "status", 
        "created_at",
        "processed_at"
    )
    search_fields = (
        "account__user__email",
        "description",
        "related_service__title"
    )
    readonly_fields = ("signed_amount", "created_at", "updated_at")
    
    fieldsets = (
        (None, {
            "fields": (
                "account", 
                "transaction_type", 
                "amount",
                "signed_amount",
                "status"
            )
        }),
        ("Details", {
            "fields": ("description",)
        }),
        ("Related Objects", {
            "fields": (
                "related_service",
                "related_session", 
                "related_completion"
            ),
            "classes": ("collapse",)
        }),
        ("Processing", {
            "fields": ("processed_by", "processed_at")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
