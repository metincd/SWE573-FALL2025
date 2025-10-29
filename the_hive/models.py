from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
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
