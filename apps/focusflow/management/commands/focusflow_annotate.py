"""
Management command: FocusFlow AI summarization trigger
------------------------------------------------------

Usage examples:
  python manage.py focusflow_annotate --conversation 12
  python manage.py focusflow_annotate --message 45
  python manage.py focusflow_annotate --all-conversations
"""

from django.core.management.base import BaseCommand, CommandError
from apps.focusflow.services.summarizer import SummarizerService
from apps.focusflow.models import Conversation, Message


class Command(BaseCommand):
    help = "Annotate a FocusFlow conversation or message using the AI summarizer."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--conversation", type=int, help="Conversation ID to annotate")
        group.add_argument("--message", type=int, help="Message ID to annotate")
        group.add_argument("--all-conversations", action="store_true", help="Annotate all conversations")

        parser.add_argument("--no-tasks", action="store_true", help="Skip creating Task objects")
        parser.add_argument("--model", default="simple-v1", help="Summarizer model name label")

    def handle(self, *args, **opts):
        svc = SummarizerService(model_name=opts["model"])
        create_tasks = not opts["no-tasks"]

        if opts["conversation"]:
            conv_id = opts["conversation"]
            try:
                result = svc.annotate_conversation(conv_id, create_tasks=create_tasks)
                self._print_result("conversation", conv_id, result)
            except Conversation.DoesNotExist:
                raise CommandError(f"Conversation {conv_id} not found")

        elif opts["message"]:
            msg_id = opts["message"]
            try:
                result = svc.annotate_message(msg_id, create_tasks=create_tasks)
                self._print_result("message", msg_id, result)
            except Message.DoesNotExist:
                raise CommandError(f"Message {msg_id} not found")

        elif opts["all_conversations"]:
            qs = Conversation.objects.order_by("-last_message_at")[:50]
            total = qs.count()
            self.stdout.write(f"Annotating {total} conversations ...")
            for c in qs:
                result = svc.annotate_conversation(c.id, create_tasks=create_tasks)
                self.stdout.write(f"→ {c.id}: {len(result.actions)} actions, priority={result.priority_label}")
            self.stdout.write(self.style.SUCCESS("All done!"))

    def _print_result(self, kind: str, obj_id: int, result):
        self.stdout.write(
            self.style.SUCCESS(
                f"\nAI summary created for {kind} {obj_id}:"
                f"\n  Priority: {result.priority_label} ({result.priority_score:.2f})"
                f"\n  Summary: {result.summary[:250]}..."
                f"\n  Actions: {len(result.actions)} item(s)"
            )
        )