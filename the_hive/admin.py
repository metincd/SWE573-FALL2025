from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import (
    User, Profile, Tag, Service, ServiceRequest, 
    ServiceSession, Completion, TimeAccount, TimeTransaction,
    Conversation, Message, Thread, Post, ThankYouNote
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


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("created_at", "read_at", "is_recent")
    fields = (
        "sender",
        "body",
        "is_read",
        "read_at",
        "is_recent",
        "created_at"
    )


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "related_service",
        "is_archived",
        "participant_count",
        "last_message_preview",
        "created_at",
        "updated_at"
    )
    list_filter = ("is_archived", "created_at", "updated_at")
    search_fields = (
        "title",
        "related_service__title",
        "participants__email",
        "messages__body"
    )
    filter_horizontal = ("participants",)
    readonly_fields = ("last_message", "created_at", "updated_at")
    inlines = [MessageInline]
    
    fieldsets = (
        (None, {
            "fields": ("participants", "title", "is_archived")
        }),
        ("Related", {
            "fields": ("related_service",)
        }),
        ("Info", {
            "fields": ("last_message",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = "Participants"

    def last_message_preview(self, obj):
        last_msg = obj.last_message
        if last_msg:
            preview = last_msg.body[:30] + "..." if len(last_msg.body) > 30 else last_msg.body
            return f"{last_msg.sender.email}: {preview}"
        return "-"
    last_message_preview.short_description = "Last Message"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "conversation",
        "sender",
        "body_preview",
        "is_read",
        "is_recent",
        "created_at",
        "read_at"
    )
    list_filter = ("is_read", "created_at", "read_at")
    search_fields = (
        "conversation__title",
        "sender__email",
        "body"
    )
    readonly_fields = ("is_recent", "created_at", "updated_at")
    
    fieldsets = (
        (None, {
            "fields": ("conversation", "sender")
        }),
        ("Content", {
            "fields": ("body",)
        }),
        ("Status", {
            "fields": ("is_read", "read_at", "is_recent")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def body_preview(self, obj):
        return obj.body[:50] + "..." if len(obj.body) > 50 else obj.body
    body_preview.short_description = "Message Preview"


# Forum Admin

class PostInline(admin.TabularInline):
    model = Post
    extra = 0
    readonly_fields = ("is_recent", "created_at")
    fields = (
        "author",
        "body",
        "status",
        "is_flagged",
        "is_recent",
        "created_at"
    )


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "status",
        "is_flagged",
        "post_count",
        "views_count",
        "is_active",
        "created_at",
        "updated_at"
    )
    list_filter = (
        "status",
        "is_flagged",
        "created_at",
        "updated_at",
        "tags"
    )
    search_fields = (
        "title",
        "author__email",
        "posts__body",
        "flagged_reason"
    )
    filter_horizontal = ("tags",)
    readonly_fields = (
        "post_count",
        "last_post",
        "is_active",
        "views_count",
        "created_at",
        "updated_at"
    )
    inlines = [PostInline]
    
    fieldsets = (
        (None, {
            "fields": ("title", "author", "status")
        }),
        ("Content", {
            "fields": ("tags", "related_service")
        }),
        ("Flagging", {
            "fields": (
                "is_flagged",
                "flagged_reason",
                "flagged_by",
                "flagged_at"
            ),
            "classes": ("collapse",)
        }),
        ("Statistics", {
            "fields": ("views_count", "post_count", "is_active", "last_post"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def post_count(self, obj):
        return obj.post_count
    post_count.short_description = "Posts"

    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = "Active"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "thread",
        "author",
        "body_preview",
        "status",
        "is_flagged",
        "is_recent",
        "created_at"
    )
    list_filter = (
        "status",
        "is_flagged",
        "created_at",
        "thread__status"
    )
    search_fields = (
        "thread__title",
        "author__email",
        "body",
        "flagged_reason"
    )
    readonly_fields = ("is_recent", "created_at", "updated_at")
    
    fieldsets = (
        (None, {
            "fields": ("thread", "author", "status")
        }),
        ("Content", {
            "fields": ("body",)
        }),
        ("Flagging", {
            "fields": (
                "is_flagged",
                "flagged_reason",
                "flagged_by",
                "flagged_at"
            ),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("is_recent", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def body_preview(self, obj):
        return obj.body[:50] + "..." if len(obj.body) > 50 else obj.body
    body_preview.short_description = "Post Preview"

    def is_recent(self, obj):
        return obj.is_recent
    is_recent.boolean = True
    is_recent.short_description = "Recent"


@admin.register(ThankYouNote)
class ThankYouNoteAdmin(admin.ModelAdmin):
    list_display = (
        "from_user",
        "to_user",
        "message_preview",
        "status",
        "related_service",
        "is_unread",
        "created_at",
        "read_at"
    )
    list_filter = (
        "status",
        "created_at",
        "read_at",
        "related_service"
    )
    search_fields = (
        "from_user__email",
        "to_user__email",
        "message",
        "related_service__title"
    )
    readonly_fields = (
        "message_preview",
        "is_unread",
        "created_at",
        "updated_at"
    )
    
    fieldsets = (
        (None, {
            "fields": ("from_user", "to_user", "status")
        }),
        ("Content", {
            "fields": ("message", "message_preview")
        }),
        ("Related Objects", {
            "fields": ("related_service", "related_session"),
            "classes": ("collapse",)
        }),
        ("Status", {
            "fields": ("is_unread", "read_at")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def message_preview(self, obj):
        return obj.message_preview
    message_preview.short_description = "Message Preview"

    def is_unread(self, obj):
        return obj.is_unread
    is_unread.boolean = True
    is_unread.short_description = "Unread"
