from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.focusflow.models import (
    Workspace,
    WorkspaceMember,
    Contact,
    Stream,
    Conversation,
    Message,
    Task,
    Integration,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed dummy FocusFlow data (safe for demo)"

    def handle(self, *args, **options):
        # --- demo user ---
        user, _ = User.objects.get_or_create(username="demo_user", defaults={"email": "demo@example.com"})
        workspace, _ = Workspace.objects.get_or_create(
            name="Demo Workspace",
            owner=user,
            defaults={"slug": "demo-workspace"},
        )

        # --- members & integrations ---
        WorkspaceMember.objects.get_or_create(workspace=workspace, user=user)
        gmail_integration, _ = Integration.objects.get_or_create(
            workspace=workspace,
            provider="gmail",
            account_label="demo@example.com",
        )

        # --- streams ---
        stream, _ = Stream.objects.get_or_create(
            integration=gmail_integration,
            category="email",
            kind="Inbox",
            remote_id="inbox-001",
            name="Inbox",
        )

        # --- contacts ---
        alice, _ = Contact.objects.get_or_create(workspace=workspace, display_name="Alice Johnson")
        bob, _ = Contact.objects.get_or_create(workspace=workspace, display_name="Bob Lee")

        # --- conversations ---
        conv1, _ = Conversation.objects.get_or_create(
            workspace=workspace,
            stream=stream,
            remote_thread_id="thread-101",
            subject="Welcome to FocusFlow Demo",
            priority="action",
            unread_count=2,
            last_message_at=timezone.now(),
        )

        conv2, _ = Conversation.objects.get_or_create(
            workspace=workspace,
            stream=stream,
            remote_thread_id="thread-102",
            subject="Weekly Report Review",
            priority="urgent",
            unread_count=1,
            last_message_at=timezone.now(),
        )

        # --- messages ---
        Message.objects.get_or_create(
            conversation=conv1,
            stream=stream,
            remote_message_id="msg-101",
            sender=alice,
            text="Hey! Here's a demo email message so you can see summaries.",
            sent_at=timezone.now(),
        )

        Message.objects.get_or_create(
            conversation=conv2,
            stream=stream,
            remote_message_id="msg-102",
            sender=bob,
            text="Don't forget to submit the weekly report by Friday.",
            sent_at=timezone.now(),
        )

        # --- tasks ---
        Task.objects.get_or_create(
            workspace=workspace,
            title="Reply to Alice",
            status="todo",
            source_object_id=1,
            source_content_type_id=1,  # safe dummy placeholder
        )

        Task.objects.get_or_create(
            workspace=workspace,
            title="Submit weekly report",
            status="doing",
            source_object_id=1,
            source_content_type_id=1,
        )

        self.stdout.write(self.style.SUCCESS("✅ FocusFlow demo data seeded successfully!"))