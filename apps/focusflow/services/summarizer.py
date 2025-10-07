"""
FocusFlow Summarization & Action Extraction (lightweight, no extra deps)

What it does
------------
- Summarizes message/conversation text (simple frequency-based, sentence ranking)
- Extracts action items with rules (imperatives, "please", "need to", due hints)
- Heuristically classifies priority (urgent/action/fyi/spam) with a confidence score
- Upserts AIAnnotation rows (SUMMARY / PRIORITY / ACTION_ITEMS)
- Creates Task rows from extracted action items (deduped by title+source)

Design goals
------------
- No new dependencies (pure Python); safe to run on local dev
- Idempotent: won't spam-duplicate annotations or tasks
- Pluggable: later you can swap `summarize_text()` with a Hugging Face model

Usage
-----
from apps.focusflow.services.summarizer import SummarizerService
svc = SummarizerService(model_name="simple-v1")

# For a conversation:
result = svc.annotate_conversation(conversation_id=123, create_tasks=True)

# For a single message:
result = svc.annotate_message(message_id=456, create_tasks=True)
"""

from __future__ import annotations

import html as _html
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from ..models import (
    AIAnnotation,
    Conversation,
    Message,
    Task,
    Workspace,
)

# -------------------------
# Config (tweak as needed)
# -------------------------

DEFAULT_MAX_SUMMARY_SENTENCES = 3
DEFAULT_MIN_SENT_LEN = 30           # characters; avoid tiny/noisy sentences
DEFAULT_MAX_TEXT_CHARS = 15000      # cap input to keep it snappy in dev
DEFAULT_ACTIONS_LIMIT = 10

# Very small English stopword list (expand if you like)
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "in", "on", "for", "to", "of",
    "with", "at", "by", "from", "as", "is", "are", "was", "were", "be", "been",
    "it", "its", "this", "that", "these", "those", "i", "you", "he", "she",
    "we", "they", "them", "your", "our", "their", "my", "me", "us",
}

# Regex helpers
RE_TAGS = re.compile(r"<[^>]+>")
RE_WHITESPACE = re.compile(r"\s+")
RE_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
RE_BULLET = re.compile(r"^\s*[-*•]\s+", re.MULTILINE)
RE_ACTION_HINT = re.compile(
    r"\b(please|kindly|asap|urgent|due\s+(?:on|by)|deadline|follow\s*up|action\s*required|todo|to-do)\b",
    re.IGNORECASE,
)
RE_SPAM_HINT = re.compile(r"\b(unsubscribe|promo|promotion|offer|sale|discount)\b", re.IGNORECASE)


@dataclass
class SummarizeResult:
    summary: str
    actions: List[str]
    priority_label: str
    priority_score: float


class SummarizerService:
    """
    Lightweight NLP-ish service you can replace later with a real model.
    """

    def __init__(
        self,
        model_name: str = "simple-v1",
        max_summary_sentences: int = DEFAULT_MAX_SUMMARY_SENTENCES,
    ):
        self.model_name = model_name
        self.max_summary_sentences = max_summary_sentences

    # ------------- Public API (entry points) -------------

    @transaction.atomic
    def annotate_conversation(self, conversation_id: int, create_tasks: bool = True) -> SummarizeResult:
        conv = Conversation.objects.select_related("workspace").get(pk=conversation_id)
        text = self._conversation_text(conv)
        result = self._summarize_and_extract(text)

        # Upsert annotations
        self._upsert_annotation(conv.workspace, conv, AIAnnotation.Kind.SUMMARY, content_text=result.summary)
        self._upsert_annotation(
            conv.workspace,
            conv,
            AIAnnotation.Kind.PRIORITY,
            content_text=result.priority_label,
            content_json={"label": result.priority_label, "score": result.priority_score},
            score=result.priority_score,
        )
        ann = self._upsert_annotation(
            conv.workspace,
            conv,
            AIAnnotation.Kind.ACTION_ITEMS,
            content_text="\n".join(f"- {a}" for a in result.actions),
            content_json={"items": result.actions},
        )

        # Optional tasks creation (dedup by title+source)
        if create_tasks and result.actions:
            self._ensure_tasks_from_actions(
                workspace=conv.workspace,
                source_obj=conv,
                actions=result.actions,
                origin_annotation=ann,
            )

        return result

    @transaction.atomic
    def annotate_message(self, message_id: int, create_tasks: bool = False) -> SummarizeResult:
        msg = Message.objects.select_related("conversation__workspace").get(pk=message_id)
        text = self._message_text(msg)
        result = self._summarize_and_extract(text)

        ws = msg.conversation.workspace

        self._upsert_annotation(ws, msg, AIAnnotation.Kind.SUMMARY, content_text=result.summary)
        self._upsert_annotation(
            ws,
            msg,
            AIAnnotation.Kind.PRIORITY,
            content_text=result.priority_label,
            content_json={"label": result.priority_label, "score": result.priority_score},
            score=result.priority_score,
        )
        ann = self._upsert_annotation(
            ws,
            msg,
            AIAnnotation.Kind.ACTION_ITEMS,
            content_text="\n".join(f"- {a}" for a in result.actions),
            content_json={"items": result.actions},
        )

        if create_tasks and result.actions:
            self._ensure_tasks_from_actions(
                workspace=ws,
                source_obj=msg,
                actions=result.actions,
                origin_annotation=ann,
            )

        return result

    # ------------- Core logic -------------

    def _summarize_and_extract(self, raw_text: str) -> SummarizeResult:
        text = self._clean_text(raw_text)[:DEFAULT_MAX_TEXT_CHARS]
        sentences = self._split_sentences(text)

        summary = self._summarize_sentences(sentences, self.max_summary_sentences)
        actions = self._extract_action_items(text, sentences, limit=DEFAULT_ACTIONS_LIMIT)
        label, score = self._priority_heuristic(text, actions)

        return SummarizeResult(summary=summary, actions=actions, priority_label=label, priority_score=score)

    # ------------- Text builders -------------

    def _conversation_text(self, conv: Conversation) -> str:
        parts: List[str] = []
        if conv.subject:
            parts.append(conv.subject.strip())

        # use most recent ~20 messages for a concise digest
        messages = (
            conv.messages.select_related("sender")
            .order_by("-sent_at")[:20]
            .values_list("text", "html")
        )
        for text, html in messages:
            parts.append(self._best_text(text, html))
        return "\n\n".join(p for p in parts if p)

    def _message_text(self, msg: Message) -> str:
        header = f"From: {getattr(msg.sender, 'display_name', '')}\nSent: {msg.sent_at:%Y-%m-%d %H:%M}"
        body = self._best_text(msg.text, msg.html)
        return f"{header}\n\n{body}"

    # ------------- NLP-ish utilities -------------

    @staticmethod
    def _best_text(text: Optional[str], html: Optional[str]) -> str:
        if text and text.strip():
            return text.strip()
        if html and html.strip():
            return SummarizerService._strip_html(html)
        return ""

    @staticmethod
    def _strip_html(html: str) -> str:
        # quick+safe HTML → text
        unescaped = _html.unescape(html or "")
        no_tags = RE_TAGS.sub(" ", unescaped)
        collapsed = RE_WHITESPACE.sub(" ", no_tags)
        return collapsed.strip()

    @staticmethod
    def _clean_text(text: str) -> str:
        return RE_WHITESPACE.sub(" ", (text or "")).strip()

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        if not text:
            return []
        # keep original order; naive split
        raw = RE_SENTENCE_SPLIT.split(text)
        # filter very short/noisy sentences
        return [s.strip() for s in raw if len(s.strip()) >= DEFAULT_MIN_SENT_LEN]

    @staticmethod
    def _tokenize_words(text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"[A-Za-z0-9']+", text)]

    def _summarize_sentences(self, sentences: Sequence[str], k: int) -> str:
        if not sentences:
            return ""
        # score sentences by word frequency (minus stopwords), select top-k in original order
        all_words = self._tokenize_words(" ".join(sentences))
        freqs = Counter(w for w in all_words if w not in STOPWORDS)

        scored = []
        for idx, s in enumerate(sentences):
            words = self._tokenize_words(s)
            score = sum(freqs.get(w, 0) for w in words)
            scored.append((idx, score, s))

        # pick top-k by score, but sort back by original index to keep flow
        top = sorted(sorted(scored, key=lambda x: x[1], reverse=True)[:k], key=lambda x: x[0])
        return " ".join(s for _, __, s in top)

    def _extract_action_items(self, text: str, sentences: Sequence[str], limit: int = 10) -> List[str]:
        actions: List[str] = []

        # 1) bullets are strong action hints
        for line in text.splitlines():
            if RE_BULLET.match(line) or RE_ACTION_HINT.search(line):
                cleaned = RE_BULLET.sub("", line).strip()
                if cleaned and cleaned not in actions:
                    actions.append(self._normalize_action(cleaned))
            if len(actions) >= limit:
                return actions[:limit]

        # 2) imperative/requests in sentences
        imperative_verbs = (
            "please ", "kindly ", "let's ", "lets ", "we should ", "you should ",
            "need to ", "must ", "can you ", "action required", "follow up",
        )
        for s in sentences:
            low = s.lower()
            if any(v in low for v in imperative_verbs) or RE_ACTION_HINT.search(s):
                norm = self._normalize_action(s)
                if norm and norm not in actions:
                    actions.append(norm)
            if len(actions) >= limit:
                break

        return actions[:limit]

    @staticmethod
    def _normalize_action(text: str) -> str:
        t = text.strip()
        # trim trailing periods and excessive spaces
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"[.·•\-\*]+$", "", t).strip()
        # cap to a reasonable title length for Task.title
        return (t[:240]).strip()

    def _priority_heuristic(self, text: str, actions: Sequence[str]) -> Tuple[str, float]:
        low = text.lower()
        # spam?
        if RE_SPAM_HINT.search(low):
            return ("spam", 0.85)
        # urgent?
        if "asap" in low or "urgent" in low or "immediately" in low:
            return ("urgent", 0.9)
        # action if we detected actionable items
        if actions:
            return ("action", 0.7)
        # otherwise fyi
        return ("fyi", 0.6)

    # ------------- Persistence helpers -------------

    def _upsert_annotation(
        self,
        workspace: Workspace,
        target_obj,
        kind: str,
        *,
        content_text: str = "",
        content_json: Optional[dict] = None,
        score: Optional[float] = None,
    ) -> AIAnnotation:
        """Upsert by (workspace, kind, target_content_type, target_object_id, model_name)."""
        content_json = content_json or {}
        ct = ContentType.objects.get_for_model(type(target_obj))
        anno, created = AIAnnotation.objects.update_or_create(
            workspace=workspace,
            kind=kind,
            target_content_type=ct,
            target_object_id=target_obj.pk,
            model_name=self.model_name,
            defaults={
                "content_text": content_text or "",
                "content_json": content_json,
                "score": score,
                "updated_at": timezone.now(),
            },
        )
        return anno

    def _ensure_tasks_from_actions(
        self,
        *,
        workspace: Workspace,
        source_obj,
        actions: Sequence[str],
        origin_annotation: Optional[AIAnnotation] = None,
    ) -> List[Task]:
        """Create Task rows for each action if not already present (by title+source, not DONE/DISMISSED)."""
        ct = ContentType.objects.get_for_model(type(source_obj))
        created_tasks: List[Task] = []

        for title in actions:
            exists = Task.objects.filter(
                workspace=workspace,
                source_content_type=ct,
                source_object_id=source_obj.pk,
                title=title,
                is_deleted=False,
            ).exclude(status=Task.Status.DONE).exists()

            if exists:
                continue

            t = Task.objects.create(
                workspace=workspace,
                source_content_type=ct,
                source_object_id=source_obj.pk,
                title=title,
                status=Task.Status.TODO,
                origin_annotation=origin_annotation,
                confidence=0.65,  # heuristic confidence; tune if you like
            )
            created_tasks.append(t)

        return created_tasks