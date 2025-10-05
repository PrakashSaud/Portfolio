from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify


# ---------------------------
# Base & mixins
# ---------------------------

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


# ---------------------------
# Tenancy / membership
# ---------------------------

class Workspace(TimeStampedModel, SoftDeleteMixin):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_workspaces"
    )

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["owner", "created_at"]),
        ]
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class WorkspaceMember(TimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspace_memberships")
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("workspace", "user")]
        indexes = [
            models.Index(fields=["workspace", "role"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.workspace} ({self.role})"


# ---------------------------
# Integrations & streams
# ---------------------------

class Integration(TimeStampedModel):
    class Provider(models.TextChoices):
        GMAIL = "gmail", "Gmail"
        SLACK = "slack", "Slack"
        TEAMS = "teams", "Microsoft Teams"
        WHATSAPP = "whatsapp", "WhatsApp"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ERROR = "error", "Error"
        DISCONNECTED = "disconnected", "Disconnected"

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="integrations")
    provider = models.CharField(max_length=24, choices=Provider.choices)
    account_label = models.CharField(max_length=190, help_text="Display label (e.g., email address or workspace name)")
    scopes_json = models.JSONField(default=list, blank=True)
    secrets_ref = models.CharField(max_length=190, blank=True, help_text="Reference to encrypted credential store")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    sync_status = models.CharField(max_length=20, default="idle")
    last_error = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["workspace", "provider"]),
            models.Index(fields=["status"]),
        ]
        unique_together = [("workspace", "provider", "account_label")]

    def __str__(self) -> str:
        return f"{self.get_provider_display()} – {self.account_label}"


class Stream(TimeStampedModel):
    class Category(models.TextChoices):
        EMAIL = "email", "Email"
        CHAT = "chat", "Chat"
        SMS = "sms", "SMS"
        OTHER = "other", "Other"

    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, related_name="streams")
    category = models.CharField(max_length=16, choices=Category.choices, default=Category.EMAIL)
    kind = models.CharField(max_length=48, help_text="Label/Channel/DM, etc.")
    remote_id = models.CharField(max_length=190, help_text="Provider-side id")
    name = models.CharField(max_length=190, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("integration", "remote_id")]
        indexes = [
            models.Index(fields=["integration", "category"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.name or f"{self.integration}:{self.kind}"


class SyncCursor(TimeStampedModel):
    stream = models.OneToOneField(Stream, on_delete=models.CASCADE, related_name="cursor")
    cursor = models.TextField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default="idle")
    last_error_message = models.TextField(blank=True)
    last_duration_ms = models.PositiveIntegerField(default=0)
    stats_json = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Cursor(stream={self.stream_id})"


# ---------------------------
# People graph
# ---------------------------

class Contact(TimeStampedModel, SoftDeleteMixin):
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="contacts", null=True, blank=True,
        help_text="Null = global contact"
    )
    display_name = models.CharField(max_length=190, blank=True)
    avatar_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["workspace", "display_name"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return self.display_name or f"Contact#{self.pk}"


class Identity(TimeStampedModel):
    class Kind(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"
        SLACK = "slack", "Slack"
        TEAMS = "teams", "Teams"
        WHATSAPP = "whatsapp", "WhatsApp"
        OTHER = "other", "Other"

    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="identities")
    kind = models.CharField(max_length=24, choices=Kind.choices)
    value = models.CharField(max_length=190)
    normalized_value = models.CharField(max_length=190)

    class Meta:
        unique_together = [("kind", "normalized_value")]
        indexes = [models.Index(fields=["contact", "kind"])]

    def __str__(self) -> str:
        return f"{self.kind}:{self.value}"


# ---------------------------
# Conversations & messages
# ---------------------------

class Conversation(TimeStampedModel, SoftDeleteMixin):
    class Priority(models.TextChoices):
        URGENT = "urgent", "Urgent"
        ACTION = "action", "Action"
        FYI = "fyi", "FYI"
        SPAM = "spam", "Spam"

    class State(models.TextChoices):
        OPEN = "open", "Open"
        SNOOZED = "snoozed", "Snoozed"
        ARCHIVED = "archived", "Archived"

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="conversations")
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name="conversations")
    remote_thread_id = models.CharField(max_length=190)
    subject = models.CharField(max_length=300, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)
    unread_count = models.PositiveIntegerField(default=0)
    priority = models.CharField(max_length=12, choices=Priority.choices, default=Priority.FYI)
    state = models.CharField(max_length=12, choices=State.choices, default=State.OPEN)
    importance_score = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    is_starred = models.BooleanField(default=False)
    hash_key = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [("stream", "remote_thread_id")]
        indexes = [
            models.Index(fields=["workspace", "state"]),
            models.Index(fields=["stream", "-last_message_at"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["is_starred"]),
        ]
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self) -> str:
        return self.subject or f"Conversation#{self.pk}"


class ConversationParticipant(models.Model):
    class Role(models.TextChoices):
        ORIGINATOR = "originator", "Originator"
        MEMBER = "member", "Member"
        EXTERNAL = "external", "External"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="participants")
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="conversation_participations")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)

    class Meta:
        unique_together = [("conversation", "contact")]
        indexes = [models.Index(fields=["conversation"]), models.Index(fields=["contact", "role"])]

    def __str__(self) -> str:
        return f"{self.contact} in {self.conversation} ({self.role})"


class Message(TimeStampedModel, SoftDeleteMixin):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name="messages")
    remote_message_id = models.CharField(max_length=190)
    sender = models.ForeignKey(Contact, on_delete=models.PROTECT, related_name="sent_messages")
    sent_at = models.DateTimeField(db_index=True)
    text = models.TextField(blank=True)
    html = models.TextField(blank=True)
    is_from_me = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    external_url = models.URLField(blank=True)
    ingested_at = models.DateTimeField(auto_now_add=True)
    thread_index = models.IntegerField(null=True, blank=True, help_text="Order inside thread if provider supplies one")
    vector_id = models.CharField(max_length=64, blank=True, help_text="Reference to embeddings/vector store")
    reactions_json = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [("stream", "remote_message_id")]
        indexes = [
            models.Index(fields=["conversation", "-sent_at"]),
            models.Index(fields=["stream", "-sent_at"]),
            models.Index(fields=["sender", "sent_at"]),
        ]
        ordering = ["-sent_at", "-created_at"]

    def __str__(self) -> str:
        return f"{self.sender}: {self.text[:60] if self.text else self.subject_fallback}"

    @property
    def subject_fallback(self) -> str:
        return (self.html or self.text or "")[:60]


class MessageRecipient(models.Model):
    class RType(models.TextChoices):
        TO = "to", "To"
        CC = "cc", "Cc"
        BCC = "bcc", "Bcc"
        CHANNEL = "channel", "Channel"

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="recipients")
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="received_messages")
    rtype = models.CharField(max_length=12, choices=RType.choices, default=RType.TO)

    class Meta:
        indexes = [models.Index(fields=["message"]), models.Index(fields=["contact", "rtype"])]
        unique_together = [("message", "contact", "rtype")]

    def __str__(self) -> str:
        return f"{self.rtype} {self.contact} on {self.message_id}"


class Attachment(TimeStampedModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="focusflow/attachments/%Y/%m/")
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True)

    class Meta:
        indexes = [models.Index(fields=["message"])]

    def __str__(self) -> str:
        return self.filename


# ---------------------------
# Tags (conversation & message)
# ---------------------------

class Tag(TimeStampedModel):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=60)
    slug = models.SlugField(max_length=80)
    color = models.CharField(max_length=16, blank=True)

    class Meta:
        unique_together = [("workspace", "slug")]
        indexes = [models.Index(fields=["workspace", "name"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class ConversationTag(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="conversation_tags")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="conversation_tags")

    class Meta:
        unique_together = [("conversation", "tag")]
        indexes = [models.Index(fields=["tag"]), models.Index(fields=["conversation"])]


class MessageTag(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="message_tags")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="message_tags")

    class Meta:
        unique_together = [("message", "tag")]
        indexes = [models.Index(fields=["tag"]), models.Index(fields=["message"])]


# ---------------------------
# AI layer
# ---------------------------

class AIAnnotation(TimeStampedModel):
    """
    Generic AI artifact: summary, sentiment, priority, extracted entities, action items, etc.
    Targeted via GenericForeignKey so we can annotate Conversations or Messages.
    """
    class Kind(models.TextChoices):
        SUMMARY = "summary", "Summary"
        PRIORITY = "priority", "Priority"
        SENTIMENT = "sentiment", "Sentiment"
        ENTITIES = "entities", "Entities"
        ACTION_ITEMS = "action_items", "Action Items"
        OTHER = "other", "Other"

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="ai_annotations")
    # Generic target
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id = models.PositiveBigIntegerField()
    target = GenericForeignKey("target_content_type", "target_object_id")

    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.SUMMARY)
    content_text = models.TextField(blank=True)
    content_json = models.JSONField(default=dict, blank=True)
    score = models.FloatField(null=True, blank=True)
    model_name = models.CharField(max_length=120, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["workspace", "created_at"]),
            models.Index(fields=["target_content_type", "target_object_id"]),
            models.Index(fields=["kind"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind} on {self.target_content_type_id}:{self.target_object_id}"


class Task(TimeStampedModel, SoftDeleteMixin):
    class Status(models.TextChoices):
        TODO = "todo", "To Do"
        DOING = "doing", "Doing"
        DONE = "done", "Done"
        DISMISSED = "dismissed", "Dismissed"

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="tasks")

    # Source link (conversation or message)
    source_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    source_object_id = models.PositiveBigIntegerField()
    source = GenericForeignKey("source_content_type", "source_object_id")

    title = models.CharField(max_length=240)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.TODO)
    due_at = models.DateTimeField(null=True, blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="focusflow_tasks"
    )
    origin_annotation = models.ForeignKey(
        AIAnnotation, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )
    confidence = models.FloatField(null=True, blank=True,
                                   validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    class Meta:
        indexes = [
            models.Index(fields=["workspace", "status"]),
            models.Index(fields=["due_at"]),
            models.Index(fields=["assignee"]),
        ]

    def __str__(self) -> str:
        return self.title