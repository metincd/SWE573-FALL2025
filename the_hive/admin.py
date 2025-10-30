from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone
from .models import (
    User, Profile, Tag, Service, ServiceRequest, 
    ServiceSession, Completion, TimeAccount, TimeTransaction,
    Conversation, Message, Thread, Post, ThankYouNote,
    Report, ModerationAction, Notification, Review, 
    ReviewHelpfulVote, UserRating
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


class ModerationActionInline(admin.TabularInline):
    model = ModerationAction
    extra = 0
    readonly_fields = ("is_active", "is_expired", "created_at")
    fields = (
        "moderator",
        "action",
        "severity",
        "affected_user",
        "is_active",
        "is_expired",
        "created_at"
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "reporter",
        "reason",
        "status",
        "reported_content_preview",
        "is_pending",
        "created_at",
        "resolved_at"
    )
    list_filter = (
        "reason",
        "status",
        "content_type",
        "created_at",
        "resolved_at"
    )
    search_fields = (
        "reporter__email",
        "description",
        "reason",
        "evidence_url"
    )
    readonly_fields = (
        "reported_object",
        "reported_content_preview",
        "is_pending",
        "created_at",
        "updated_at"
    )
    inlines = [ModerationActionInline]
    
    fieldsets = (
        (None, {
            "fields": ("reporter", "status")
        }),
        ("Reported Content", {
            "fields": (
                "content_type",
                "object_id", 
                "reported_object",
                "reported_content_preview"
            )
        }),
        ("Report Details", {
            "fields": ("reason", "description", "evidence_url")
        }),
        ("Tracking", {
            "fields": ("reporter_ip", "is_pending"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "resolved_at"),
            "classes": ("collapse",)
        }),
    )

    def reported_content_preview(self, obj):
        return obj.reported_content_preview
    reported_content_preview.short_description = "Content Preview"

    def is_pending(self, obj):
        return obj.is_pending
    is_pending.boolean = True
    is_pending.short_description = "Pending"

    actions = ['resolve_reports', 'dismiss_reports']

    def resolve_reports(self, request, queryset):
        """Bulk resolve reports"""
        count = 0
        for report in queryset:
            if report.is_pending:
                report.resolve(resolved_by=request.user)
                count += 1
        
        self.message_user(
            request,
            f"Successfully resolved {count} reports."
        )
    resolve_reports.short_description = "Resolve selected reports"

    def dismiss_reports(self, request, queryset):
        """Bulk dismiss reports"""
        count = 0
        for report in queryset:
            if report.is_pending:
                report.dismiss(dismissed_by=request.user)
                count += 1
        
        self.message_user(
            request,
            f"Successfully dismissed {count} reports."
        )
    dismiss_reports.short_description = "Dismiss selected reports"


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = (
        "moderator",
        "action",
        "severity",
        "affected_user",
        "is_active",
        "is_expired",
        "is_reversed",
        "created_at",
        "expires_at"
    )
    list_filter = (
        "action",
        "severity",
        "is_reversed",
        "created_at",
        "expires_at"
    )
    search_fields = (
        "moderator__email",
        "affected_user__email",
        "notes",
        "reversal_reason"
    )
    readonly_fields = (
        "is_active",
        "is_expired",
        "created_at",
        "updated_at"
    )
    
    fieldsets = (
        (None, {
            "fields": ("moderator", "action", "severity")
        }),
        ("Target", {
            "fields": ("report", "affected_user")
        }),
        ("Details", {
            "fields": ("notes", "duration_days", "expires_at")
        }),
        ("Status", {
            "fields": ("is_active", "is_expired", "is_reversed")
        }),
        ("Reversal", {
            "fields": ("reversed_by", "reversed_at", "reversal_reason"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = "Active"

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = "Expired"

    actions = ['reverse_actions']

    def reverse_actions(self, request, queryset):
        """Bulk reverse moderation actions"""
        count = 0
        for action in queryset:
            if action.is_active and not action.is_reversed:
                action.reverse(
                    reversed_by=request.user,
                    reason=f"Bulk reversal by admin {request.user.email}"
                )
                count += 1
        
        self.message_user(
            request,
            f"Successfully reversed {count} moderation actions."
        )
    reverse_actions.short_description = "Reverse selected actions"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "notification_type",
        "title",
        "priority",
        "is_read",
        "is_dismissed",
        "is_sent",
        "is_active_status",
        "age_display",
        "created_at"
    )
    list_filter = (
        "notification_type",
        "priority",
        "is_read",
        "is_dismissed",
        "is_sent",
        "created_at",
        "expires_at"
    )
    search_fields = (
        "user__email",
        "title",
        "message",
        "notification_type"
    )
    readonly_fields = (
        "age_display",
        "is_active_status",
        "is_unread_status",
        "is_expired_status",
        "is_urgent_status",
        "created_at",
        "updated_at",
        "read_at",
        "dismissed_at",
        "sent_at"
    )
    
    fieldsets = (
        (None, {
            "fields": ("user", "notification_type", "priority")
        }),
        ("Content", {
            "fields": ("title", "message", "payload")
        }),
        ("Related Objects", {
            "fields": ("related_service", "related_conversation", "related_thread"),
            "classes": ("collapse",)
        }),
        ("Status", {
            "fields": (
                "is_read", "read_at",
                "is_dismissed", "dismissed_at",
                "is_sent", "sent_at", "delivery_channels"
            )
        }),
        ("Status Info", {
            "fields": (
                "is_active_status", "is_unread_status", 
                "is_expired_status", "is_urgent_status", "age_display"
            ),
            "classes": ("collapse",)
        }),
        ("Expiry", {
            "fields": ("expires_at",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def is_active_status(self, obj):
        return obj.is_active
    is_active_status.boolean = True
    is_active_status.short_description = "Active"

    def is_unread_status(self, obj):
        return obj.is_unread
    is_unread_status.boolean = True
    is_unread_status.short_description = "Unread"

    def is_expired_status(self, obj):
        return obj.is_expired
    is_expired_status.boolean = True
    is_expired_status.short_description = "Expired"

    def is_urgent_status(self, obj):
        return obj.is_urgent
    is_urgent_status.boolean = True
    is_urgent_status.short_description = "Urgent"

    def age_display(self, obj):
        hours = obj.age_in_hours
        if hours < 1:
            return "< 1 hour"
        elif hours < 24:
            return f"{hours} hours"
        else:
            days = hours // 24
            return f"{days} days"
    age_display.short_description = "Age"

    actions = [
        'mark_as_read',
        'mark_as_unread',
        'dismiss_notifications',
        'mark_as_sent',
        'delete_expired'
    ]

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        count = 0
        for notification in queryset:
            if not notification.is_read:
                notification.mark_as_read()
                count += 1
        
        self.message_user(
            request,
            f"Successfully marked {count} notifications as read."
        )
    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        count = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        
        self.message_user(
            request,
            f"Successfully marked {count} notifications as unread."
        )
    mark_as_unread.short_description = "Mark selected notifications as unread"

    def dismiss_notifications(self, request, queryset):
        """Dismiss selected notifications"""
        count = 0
        for notification in queryset:
            if not notification.is_dismissed:
                notification.dismiss()
                count += 1
        
        self.message_user(
            request,
            f"Successfully dismissed {count} notifications."
        )
    dismiss_notifications.short_description = "Dismiss selected notifications"

    def mark_as_sent(self, request, queryset):
        """Mark selected notifications as sent"""
        count = 0
        for notification in queryset:
            if not notification.is_sent:
                notification.mark_as_sent(channels=["admin"])
                count += 1
        
        self.message_user(
            request,
            f"Successfully marked {count} notifications as sent."
        )
    mark_as_sent.short_description = "Mark selected notifications as sent"

    def delete_expired(self, request, queryset):
        """Delete expired notifications"""
        from django.utils import timezone
        expired_count = queryset.filter(
            expires_at__lt=timezone.now()
        ).count()
        
        queryset.filter(expires_at__lt=timezone.now()).delete()
        
        self.message_user(
            request,
            f"Successfully deleted {expired_count} expired notifications."
        )
    delete_expired.short_description = "Delete expired notifications"

    # Override get_queryset for performance
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'related_service', 'related_conversation', 'related_thread'
        )


class ReviewHelpfulVoteInline(admin.TabularInline):
    model = ReviewHelpfulVote
    extra = 0
    readonly_fields = ("user", "created_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "reviewer",
        "reviewee", 
        "rating_display_admin",
        "review_type",
        "related_service",
        "is_published",
        "is_flagged",
        "helpful_count",
        "is_recent_admin",
        "created_at"
    )
    list_filter = (
        "rating",
        "review_type",
        "is_published",
        "is_flagged",
        "is_anonymous",
        "is_featured",
        "created_at"
    )
    search_fields = (
        "reviewer__email",
        "reviewee__email",
        "title",
        "content",
        "related_service__title"
    )
    readonly_fields = (
        "helpful_count",
        "report_count",
        "rating_display_admin",
        "is_recent_admin",
        "created_at",
        "updated_at",
        "published_at"
    )
    inlines = [ReviewHelpfulVoteInline]
    
    fieldsets = (
        (None, {
            "fields": ("reviewer", "reviewee", "review_type")
        }),
        ("Related Objects", {
            "fields": ("related_service", "related_session", "related_completion")
        }),
        ("Review Content", {
            "fields": ("rating", "rating_display_admin", "title", "content")
        }),
        ("Settings", {
            "fields": (
                "is_anonymous", "is_verified", "is_featured",
                "is_published", "is_flagged"
            )
        }),
        ("Statistics", {
            "fields": ("helpful_count", "report_count", "is_recent_admin"),
            "classes": ("collapse",)
        }),
        ("Moderation", {
            "fields": ("moderation_notes",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "published_at"),
            "classes": ("collapse",)
        }),
    )

    def rating_display_admin(self, obj):
        return obj.rating_display
    rating_display_admin.short_description = "Rating"

    def is_recent_admin(self, obj):
        return obj.is_recent
    is_recent_admin.boolean = True
    is_recent_admin.short_description = "Recent"

    actions = ['publish_reviews', 'unpublish_reviews', 'feature_reviews', 'verify_reviews']

    def publish_reviews(self, request, queryset):
        """Publish selected reviews"""
        count = queryset.filter(is_published=False).update(
            is_published=True,
            published_at=timezone.now()
        )
        self.message_user(
            request,
            f"Successfully published {count} reviews."
        )
    publish_reviews.short_description = "Publish selected reviews"

    def unpublish_reviews(self, request, queryset):
        """Unpublish selected reviews"""
        count = queryset.filter(is_published=True).update(is_published=False)
        self.message_user(
            request,
            f"Successfully unpublished {count} reviews."
        )
    unpublish_reviews.short_description = "Unpublish selected reviews"

    def feature_reviews(self, request, queryset):
        """Feature selected reviews"""
        count = queryset.filter(is_featured=False).update(is_featured=True)
        self.message_user(
            request,
            f"Successfully featured {count} reviews."
        )
    feature_reviews.short_description = "Feature selected reviews"

    def verify_reviews(self, request, queryset):
        """Verify selected reviews"""
        count = queryset.filter(is_verified=False).update(is_verified=True)
        self.message_user(
            request,
            f"Successfully verified {count} reviews."
        )
    verify_reviews.short_description = "Verify selected reviews"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'reviewer', 'reviewee', 'related_service', 'related_session', 'related_completion'
        )


@admin.register(ReviewHelpfulVote)
class ReviewHelpfulVoteAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "review_title_preview",
        "review_rating",
        "created_at"
    )
    list_filter = ("created_at",)
    search_fields = (
        "user__email",
        "review__title",
        "review__reviewer__email",
        "review__reviewee__email"
    )
    readonly_fields = ("created_at",)
    
    fieldsets = (
        (None, {
            "fields": ("user", "review")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    def review_title_preview(self, obj):
        return obj.review.title[:50] + "..." if len(obj.review.title) > 50 else obj.review.title
    review_title_preview.short_description = "Review Title"

    def review_rating(self, obj):
        return obj.review.rating_display
    review_rating.short_description = "Rating"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'review')


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "overall_rating_display",
        "overall_review_count",
        "provider_rating_display", 
        "receiver_rating_display",
        "is_highly_rated_admin",
        "rating_level_admin",
        "last_reviewed_at"
    )
    list_filter = (
        "overall_rating",
        "provider_rating",
        "receiver_rating",
        "is_verified_reviewer",
        "last_reviewed_at"
    )
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name"
    )
    readonly_fields = (
        "overall_rating",
        "overall_review_count",
        "provider_rating",
        "provider_review_count", 
        "receiver_rating",
        "receiver_review_count",
        "service_quality_rating",
        "service_quality_review_count",
        "rating_distribution",
        "last_reviewed_at",
        "is_highly_rated_admin",
        "rating_level_admin",
        "created_at",
        "updated_at"
    )
    
    fieldsets = (
        (None, {
            "fields": ("user", "is_verified_reviewer")
        }),
        ("Overall Ratings", {
            "fields": (
                "overall_rating", "overall_review_count",
                "rating_level_admin", "is_highly_rated_admin"
            )
        }),
        ("Detailed Ratings", {
            "fields": (
                "provider_rating", "provider_review_count",
                "receiver_rating", "receiver_review_count", 
                "service_quality_rating", "service_quality_review_count"
            ),
            "classes": ("collapse",)
        }),
        ("Distribution", {
            "fields": ("rating_distribution",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("last_reviewed_at", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def overall_rating_display(self, obj):
        if obj.overall_rating > 0:
            return f"{obj.overall_rating:.1f}⭐"
        return "No ratings"
    overall_rating_display.short_description = "Overall Rating"

    def provider_rating_display(self, obj):
        if obj.provider_rating > 0:
            return f"{obj.provider_rating:.1f}⭐ ({obj.provider_review_count})"
        return "No ratings"
    provider_rating_display.short_description = "Provider Rating"

    def receiver_rating_display(self, obj):
        if obj.receiver_rating > 0:
            return f"{obj.receiver_rating:.1f}⭐ ({obj.receiver_review_count})"
        return "No ratings"
    receiver_rating_display.short_description = "Receiver Rating"

    def is_highly_rated_admin(self, obj):
        return obj.is_highly_rated
    is_highly_rated_admin.boolean = True
    is_highly_rated_admin.short_description = "Highly Rated"

    def rating_level_admin(self, obj):
        return obj.rating_level
    rating_level_admin.short_description = "Rating Level"

    actions = ['recalculate_ratings', 'mark_as_verified_reviewer']

    def recalculate_ratings(self, request, queryset):
        """Recalculate ratings for selected users"""
        count = 0
        for user_rating in queryset:
            user_rating.update_ratings()
            count += 1
        
        self.message_user(
            request,
            f"Successfully recalculated ratings for {count} users."
        )
    recalculate_ratings.short_description = "Recalculate ratings for selected users"

    def mark_as_verified_reviewer(self, request, queryset):
        """Mark selected users as verified reviewers"""
        count = queryset.filter(is_verified_reviewer=False).update(is_verified_reviewer=True)
        
        self.message_user(
            request,
            f"Successfully marked {count} users as verified reviewers."
        )
    mark_as_verified_reviewer.short_description = "Mark as verified reviewers"
