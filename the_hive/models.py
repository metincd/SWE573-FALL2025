from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["date_joined"]),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        fn = (self.first_name or "").strip()
        ln = (self.last_name or "").strip()
        return (fn + " " + ln).strip() or self.email


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(
        max_length=120, blank=True, help_text=_("Public name shown to others.")
    )
    bio = models.TextField(blank=True, validators=[MinLengthValidator(0)])
    avatar_url = models.URLField(blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    preferred_languages = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Profile({self.user.email})"


class Tag(models.Model):
    name = models.CharField(_("tag name"), max_length=50, unique=True)
    slug = models.SlugField(_("slug"), max_length=50, unique=True)
    description = models.TextField(_("description"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Service(models.Model):
    SERVICE_TYPES = [
        ("offer", _("Offer")),
        ("need", _("Need")),
    ]

    SERVICE_STATUS = [
        ("active", _("Active")),
        ("inactive", _("Inactive")),
        ("completed", _("Completed")),
    ]

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="services", verbose_name=_("owner")
    )
    service_type = models.CharField(
        _("service type"), max_length=10, choices=SERVICE_TYPES
    )
    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"))
    tags = models.ManyToManyField(
        Tag, related_name="services", blank=True, verbose_name=_("tags")
    )
    latitude = models.DecimalField(
        _("latitude"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        _("longitude"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    status = models.CharField(
        _("status"), max_length=20, choices=SERVICE_STATUS, default="active"
    )
    estimated_hours = models.PositiveIntegerField(
        _("estimated hours"),
        null=True,
        blank=True,
        help_text=_("Estimated time to complete this service"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("service")
        verbose_name_plural = _("services")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["service_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_service_type_display()}: {self.title}"


class ServiceRequest(models.Model):
    REQUEST_STATUS = [
        ("pending", _("Pending")),
        ("accepted", _("Accepted")),
        ("rejected", _("Rejected")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="service_requests",
        verbose_name=_("requester"),
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name=_("service"),
    )
    status = models.CharField(
        _("status"), max_length=20, choices=REQUEST_STATUS, default="pending"
    )
    message = models.TextField(
        _("message"), blank=True, help_text=_("Optional message from requester")
    )
    response_note = models.TextField(
        _("response note"), blank=True, help_text=_("Owner's response to the request")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("service request")
        verbose_name_plural = _("service requests")
        ordering = ["-created_at"]
        unique_together = ["requester", "service"]
        indexes = [
            models.Index(fields=["requester"]),
            models.Index(fields=["service"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.requester.email} -> {self.service.title}"


class ServiceSession(models.Model):
    SESSION_STATUS = [
        ("scheduled", _("Scheduled")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name=_("service request"),
    )
    scheduled_start = models.DateTimeField(_("scheduled start time"))
    scheduled_end = models.DateTimeField(_("scheduled end time"))
    actual_start = models.DateTimeField(_("actual start time"), null=True, blank=True)
    actual_end = models.DateTimeField(_("actual end time"), null=True, blank=True)
    status = models.CharField(
        _("status"), max_length=20, choices=SESSION_STATUS, default="scheduled"
    )
    notes = models.TextField(_("session notes"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("service session")
        verbose_name_plural = _("service sessions")
        ordering = ["scheduled_start"]
        indexes = [
            models.Index(fields=["service_request"]),
            models.Index(fields=["status"]),
            models.Index(fields=["scheduled_start"]),
            models.Index(fields=["actual_start"]),
        ]

    def __str__(self) -> str:
        return f"Session: {self.service_request} ({self.scheduled_start})"

    @property
    def actual_hours(self) -> float | None:
        """Calculate actual hours worked if both start and end times are recorded"""
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            return delta.total_seconds() / 3600
        return None

    @property
    def scheduled_hours(self) -> float:
        """Calculate scheduled hours"""
        delta = self.scheduled_end - self.scheduled_start
        return delta.total_seconds() / 3600


class Completion(models.Model):
    COMPLETION_STATUS = [
        ("pending", _("Pending")),
        ("confirmed", _("Confirmed")),
        ("disputed", _("Disputed")),
    ]

    session = models.OneToOneField(
        ServiceSession,
        on_delete=models.CASCADE,
        related_name="completion",
        verbose_name=_("session"),
    )
    marked_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="marked_completions",
        verbose_name=_("marked by"),
    )
    status = models.CharField(
        _("status"), max_length=20, choices=COMPLETION_STATUS, default="pending"
    )
    completion_notes = models.TextField(_("completion notes"), blank=True)
    time_transferred = models.BooleanField(
        _("time transferred"),
        default=False,
        help_text=_("Whether time has been transferred in the time banking system"),
    )
    confirmed_at = models.DateTimeField(_("confirmed at"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("completion")
        verbose_name_plural = _("completions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["session"]),
            models.Index(fields=["marked_by"]),
            models.Index(fields=["status"]),
            models.Index(fields=["time_transferred"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Completion: {self.session} - {self.get_status_display()}"


class TimeAccount(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="time_account",
        verbose_name=_("user"),
    )
    balance = models.DecimalField(
        _("balance (hours)"),
        max_digits=8,
        decimal_places=2,
        default=0.00,
        help_text=_("Current time balance in hours"),
    )
    total_earned = models.DecimalField(
        _("total earned (hours)"),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_("Total hours earned by providing services"),
    )
    total_spent = models.DecimalField(
        _("total spent (hours)"),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_("Total hours spent on receiving services"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("time account")
        verbose_name_plural = _("time accounts")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["balance"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"TimeAccount({self.user.email}): {self.balance}h"

    @property
    def is_positive_balance(self) -> bool:
        """Check if user has positive balance"""
        return self.balance > 0

    @property
    def participation_ratio(self) -> float:
        """Calculate the ratio of giving vs receiving (earned/spent)"""
        if self.total_spent == 0:
            return float("inf") if self.total_earned > 0 else 0
        return float(self.total_earned / self.total_spent)


class TimeTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("credit", _("Credit")),
        ("debit", _("Debit")),
        ("adjustment", _("Adjustment")),
        ("bonus", _("Bonus")),
    ]

    TRANSACTION_STATUS = [
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
        ("failed", _("Failed")),
    ]

    account = models.ForeignKey(
        TimeAccount,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("account"),
    )
    transaction_type = models.CharField(
        _("transaction type"), max_length=20, choices=TRANSACTION_TYPES
    )
    amount = models.DecimalField(
        _("amount (hours)"),
        max_digits=6,
        decimal_places=2,
        help_text=_("Amount in hours (always positive)"),
    )
    status = models.CharField(
        _("status"), max_length=20, choices=TRANSACTION_STATUS, default="pending"
    )
    description = models.CharField(
        _("description"), max_length=500, help_text=_("Description of the transaction")
    )

    related_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_transactions",
        verbose_name=_("related service"),
    )
    related_session = models.ForeignKey(
        ServiceSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_transactions",
        verbose_name=_("related session"),
    )
    related_completion = models.ForeignKey(
        Completion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_transactions",
        verbose_name=_("related completion"),
    )

    # Tracking
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_transactions",
        verbose_name=_("processed by"),
        help_text=_("User or admin who processed this transaction"),
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("time transaction")
        verbose_name_plural = _("time transactions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["related_service"]),
            models.Index(fields=["related_session"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        sign = "+" if self.transaction_type in ["credit", "bonus"] else "-"
        return f"{sign}{self.amount}h: {self.description}"

    def save(self, *args, **kwargs):
        if self.status == "completed" and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def signed_amount(self) -> float:
        """Return amount with appropriate sign based on transaction type"""
        if self.transaction_type in ["credit", "bonus"]:
            return float(self.amount)
        else:
            return -float(self.amount)


class Conversation(models.Model):
    participants = models.ManyToManyField(
        User,
        related_name="conversations",
        verbose_name=_("participants"),
        help_text=_("Users participating in this conversation"),
    )
    related_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
        verbose_name=_("related service"),
        help_text=_("Optional service this conversation is about"),
    )
    title = models.CharField(
        _("title"),
        max_length=200,
        blank=True,
        help_text=_("Optional conversation title"),
    )
    is_archived = models.BooleanField(
        _("is archived"),
        default=False,
        help_text=_("Whether this conversation is archived"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("conversation")
        verbose_name_plural = _("conversations")
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["related_service"]),
            models.Index(fields=["is_archived"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        if self.title:
            return self.title
        if self.related_service:
            return f"Conversation about: {self.related_service.title}"
        participant_emails = ", ".join([p.email for p in self.participants.all()[:2]])
        return f"Conversation: {participant_emails}"

    @property
    def last_message(self):
        """Get the last message in this conversation"""
        return self.messages.order_by("-created_at").first()

    @property
    def unread_count_for_user(self, user):
        """Get unread message count for a specific user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def mark_as_read_for_user(self, user):
        """Mark all messages as read for a specific user"""
        self.messages.exclude(sender=user).update(is_read=True)


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("conversation"),
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name=_("sender"),
    )
    body = models.TextField(_("message body"), help_text=_("The message content"))
    is_read = models.BooleanField(
        _("is read"),
        default=False,
        help_text=_("Whether this message has been read by recipients"),
    )
    read_at = models.DateTimeField(
        _("read at"),
        null=True,
        blank=True,
        help_text=_("When this message was first read"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["conversation"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        preview = self.body[:50] + "..." if len(self.body) > 50 else self.body
        return f"{self.sender.email}: {preview}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.conversation.save()

    def mark_as_read(self):
        """Mark this message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    @property
    def is_recent(self) -> bool:
        """Check if message was sent in the last 24 hours"""
        return (timezone.now() - self.created_at).days < 1


class Thread(models.Model):
    THREAD_STATUS = [
        ("open", _("Open")),
        ("closed", _("Closed")),
        ("pinned", _("Pinned")),
    ]

    title = models.CharField(
        _("title"),
        max_length=200,
        help_text=_("Thread title")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="authored_threads",
        verbose_name=_("author")
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=THREAD_STATUS,
        default="open"
    )
    is_flagged = models.BooleanField(
        _("is flagged"),
        default=False,
        help_text=_("Whether this thread has been flagged for moderation")
    )
    flagged_reason = models.TextField(
        _("flagged reason"),
        blank=True,
        help_text=_("Reason why this thread was flagged")
    )
    flagged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flagged_threads",
        verbose_name=_("flagged by")
    )
    flagged_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects
    related_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_threads",
        verbose_name=_("related service"),
        help_text=_("Optional service this thread is about")
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="threads",
        blank=True,
        verbose_name=_("tags")
    )
    
    views_count = models.PositiveIntegerField(
        _("views count"),
        default=0,
        help_text=_("Number of times this thread has been viewed")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("thread")
        verbose_name_plural = _("threads")
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["author"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_flagged"]),
            models.Index(fields=["related_service"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
            models.Index(fields=["views_count"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def post_count(self) -> int:
        """Get total number of posts in this thread"""
        return self.posts.count()

    @property
    def last_post(self):
        """Get the last post in this thread"""
        return self.posts.order_by('-created_at').first()

    @property
    def is_active(self) -> bool:
        """Check if thread has been active in the last 7 days"""
        if self.last_post:
            return (timezone.now() - self.last_post.created_at).days <= 7
        return (timezone.now() - self.created_at).days <= 7

    def flag(self, user, reason=""):
        """Flag this thread for moderation"""
        self.is_flagged = True
        self.flagged_by = user
        self.flagged_reason = reason
        self.flagged_at = timezone.now()
        self.save()

    def unflag(self):
        """Remove flag from this thread"""
        self.is_flagged = False
        self.flagged_by = None
        self.flagged_reason = ""
        self.flagged_at = None
        self.save()


class Post(models.Model):
    POST_STATUS = [
        ("published", _("Published")),
        ("hidden", _("Hidden")),
        ("flagged", _("Flagged")),
    ]

    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name=_("thread")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="forum_posts",
        verbose_name=_("author")
    )
    body = models.TextField(
        _("post body"),
        help_text=_("The post content")
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=POST_STATUS,
        default="published"
    )
    is_flagged = models.BooleanField(
        _("is flagged"),
        default=False,
        help_text=_("Whether this post has been flagged for moderation")
    )
    flagged_reason = models.TextField(
        _("flagged reason"),
        blank=True,
        help_text=_("Reason why this post was flagged")
    )
    flagged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flagged_posts",
        verbose_name=_("flagged by")
    )
    flagged_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("post")
        verbose_name_plural = _("posts")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["thread"]),
            models.Index(fields=["author"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_flagged"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        preview = self.body[:50] + "..." if len(self.body) > 50 else self.body
        return f"{self.author.email} in {self.thread.title}: {preview}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.thread.save()

    def flag(self, user, reason=""):
        """Flag this post for moderation"""
        self.is_flagged = True
        self.flagged_by = user
        self.flagged_reason = reason
        self.flagged_at = timezone.now()
        self.status = "flagged"
        self.save()

    def unflag(self):
        """Remove flag from this post"""
        self.is_flagged = False
        self.flagged_by = None
        self.flagged_reason = ""
        self.flagged_at = None
        self.status = "published"
        self.save()

    @property
    def is_recent(self) -> bool:
        """Check if post was created in the last 24 hours"""
        return (timezone.now() - self.created_at).days < 1


class ThankYouNote(models.Model):
    NOTE_STATUS = [
        ("sent", _("Sent")),
        ("read", _("Read")),
        ("archived", _("Archived")),
    ]

    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_thank_you_notes",
        verbose_name=_("from user")
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_thank_you_notes",
        verbose_name=_("to user")
    )
    message = models.TextField(
        _("thank you message"),
        help_text=_("Personal thank you message")
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=NOTE_STATUS,
        default="sent"
    )
    
    # Optional relationships
    related_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="thank_you_notes",
        verbose_name=_("related service"),
        help_text=_("Service this thank you note is about")
    )
    related_session = models.ForeignKey(
        ServiceSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="thank_you_notes",
        verbose_name=_("related session"),
        help_text=_("Session this thank you note is about")
    )
    
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("thank you note")
        verbose_name_plural = _("thank you notes")
        ordering = ["-created_at"]
        unique_together = ["from_user", "to_user", "related_service"]  # One thank you per service
        indexes = [
            models.Index(fields=["from_user"]),
            models.Index(fields=["to_user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["related_service"]),
            models.Index(fields=["related_session"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Thank you from {self.from_user.email} to {self.to_user.email}"

    def mark_as_read(self):
        """Mark this thank you note as read"""
        if self.status == "sent":
            self.status = "read"
            self.read_at = timezone.now()
            self.save()

    @property
    def is_unread(self) -> bool:
        """Check if this thank you note is unread"""
        return self.status == "sent"

    @property
    def message_preview(self) -> str:
        """Get a preview of the message"""
        return self.message[:100] + "..." if len(self.message) > 100 else self.message


class Report(models.Model):
    REPORT_REASONS = [
        ("spam", _("Spam")),
        ("inappropriate", _("Inappropriate Content")),
        ("harassment", _("Harassment")),
        ("fraud", _("Fraud/Scam")),
        ("violence", _("Violence/Threats")),
        ("copyright", _("Copyright Violation")),
        ("misinformation", _("Misinformation")),
        ("other", _("Other")),
    ]

    REPORT_STATUS = [
        ("pending", _("Pending")),
        ("under_review", _("Under Review")),
        ("resolved", _("Resolved")),
        ("dismissed", _("Dismissed")),
        ("escalated", _("Escalated")),
    ]

    # Reporter information
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submitted_reports",
        verbose_name=_("reporter")
    )
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("content type")
    )
    object_id = models.PositiveIntegerField(_("object id"))
    reported_object = GenericForeignKey("content_type", "object_id")
    
    # Report details
    reason = models.CharField(
        _("reason"),
        max_length=20,
        choices=REPORT_REASONS,
        help_text=_("Primary reason for this report")
    )
    description = models.TextField(
        _("description"),
        help_text=_("Detailed description of the issue")
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=REPORT_STATUS,
        default="pending"
    )
    
    # Additional metadata
    reporter_ip = models.GenericIPAddressField(
        _("reporter IP"),
        null=True,
        blank=True,
        help_text=_("IP address of the reporter for tracking")
    )
    evidence_url = models.URLField(
        _("evidence URL"),
        blank=True,
        help_text=_("Optional link to additional evidence")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("report")
        verbose_name_plural = _("reports")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["reporter"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["reason"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
        # Prevent duplicate reports from same user for same object
        unique_together = ["reporter", "content_type", "object_id"]

    def __str__(self) -> str:
        return f"Report by {self.reporter.email}: {self.get_reason_display()}"

    def resolve(self, resolved_by=None):
        """Mark this report as resolved"""
        self.status = "resolved"
        self.resolved_at = timezone.now()
        self.save()
        
        if resolved_by:
            ModerationAction.objects.create(
                report=self,
                moderator=resolved_by,
                action="resolved",
                notes=f"Report resolved by {resolved_by.email}"
            )

    def dismiss(self, dismissed_by=None):
        """Dismiss this report"""
        self.status = "dismissed"
        self.resolved_at = timezone.now()
        self.save()
        
        if dismissed_by:
            ModerationAction.objects.create(
                report=self,
                moderator=dismissed_by,
                action="dismissed",
                notes=f"Report dismissed by {dismissed_by.email}"
            )

    @property
    def is_pending(self) -> bool:
        """Check if report is still pending"""
        return self.status == "pending"

    @property
    def reported_content_preview(self) -> str:
        """Get a preview of the reported content"""
        if hasattr(self.reported_object, 'body'):
            content = self.reported_object.body
        elif hasattr(self.reported_object, 'message'):
            content = self.reported_object.message
        elif hasattr(self.reported_object, 'title'):
            content = self.reported_object.title
        elif hasattr(self.reported_object, 'description'):
            content = self.reported_object.description
        else:
            content = str(self.reported_object)
        
        return content[:100] + "..." if len(content) > 100 else content


class ModerationAction(models.Model):
    MODERATION_ACTIONS = [
        ("warning_issued", _("Warning Issued")),
        ("content_hidden", _("Content Hidden")),
        ("content_removed", _("Content Removed")),
        ("user_suspended", _("User Suspended")),
        ("user_banned", _("User Banned")),
        ("resolved", _("Report Resolved")),
        ("dismissed", _("Report Dismissed")),
        ("escalated", _("Escalated to Admin")),
        ("reinstated", _("Content Reinstated")),
        ("other", _("Other Action")),
    ]

    ACTION_SEVERITY = [
        ("low", _("Low")),
        ("medium", _("Medium")),
        ("high", _("High")),
        ("critical", _("Critical")),
    ]

    report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_actions",
        verbose_name=_("related report")
    )
    
    moderator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="moderation_actions",
        verbose_name=_("moderator")
    )
    
    affected_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_actions_received",
        verbose_name=_("affected user"),
        help_text=_("User who is affected by this moderation action")
    )
    
    action = models.CharField(
        _("action"),
        max_length=30,
        choices=MODERATION_ACTIONS,
        help_text=_("Type of moderation action taken")
    )
    severity = models.CharField(
        _("severity"),
        max_length=20,
        choices=ACTION_SEVERITY,
        default="medium",
        help_text=_("Severity level of this action")
    )
    notes = models.TextField(
        _("notes"),
        help_text=_("Detailed notes about the action taken")
    )
    
    duration_days = models.PositiveIntegerField(
        _("duration in days"),
        null=True,
        blank=True,
        help_text=_("Duration for temporary actions (suspensions, etc.)")
    )
    expires_at = models.DateTimeField(
        _("expires at"),
        null=True,
        blank=True,
        help_text=_("When this action expires (for temporary actions)")
    )
    
    is_reversed = models.BooleanField(
        _("is reversed"),
        default=False,
        help_text=_("Whether this action has been reversed")
    )
    reversed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reversed_moderation_actions",
        verbose_name=_("reversed by")
    )
    reversed_at = models.DateTimeField(null=True, blank=True)
    reversal_reason = models.TextField(
        _("reversal reason"),
        blank=True,
        help_text=_("Reason for reversing this action")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("moderation action")
        verbose_name_plural = _("moderation actions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["report"]),
            models.Index(fields=["moderator"]),
            models.Index(fields=["affected_user"]),
            models.Index(fields=["action"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["is_reversed"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        action_str = f"{self.get_action_display()} by {self.moderator.email}"
        if self.affected_user:
            action_str += f" (affects {self.affected_user.email})"
        return action_str

    def reverse(self, reversed_by, reason=""):
        """Reverse this moderation action"""
        self.is_reversed = True
        self.reversed_by = reversed_by
        self.reversed_at = timezone.now()
        self.reversal_reason = reason
        self.save()

    @property
    def is_active(self) -> bool:
        """Check if this action is currently active (not reversed or expired)"""
        if self.is_reversed:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Check if this action has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def save(self, *args, **kwargs):
        if self.duration_days and not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=self.duration_days)
        super().save(*args, **kwargs)
