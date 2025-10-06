# apps/focusflow/api.py
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from django.apps import apps
from django.core.paginator import Paginator
from django.db.models import Q, Model
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404


# --- helpers -----------------------------------------------------------------
def _get_model(*candidates: str) -> Optional[type[Model]]:
    """
    Try to resolve a model by name from either 'apps.focusflow' or 'focusflow'.
    Example: _get_model('Message', 'InboxItem')
    """
    for model_name in candidates:
        for app_label in ("apps.focusflow", "focusflow"):
            try:
                return apps.get_model(app_label, model_name)
            except LookupError:
                continue
    return None


def _field_names(ModelClass: type[Model]) -> set[str]:
    return {
        f.name
        for f in ModelClass._meta.get_fields()
        # only concrete or m2m fields (skip reverse relations without .attname)
        if getattr(f, "attname", None) or getattr(f, "many_to_many", False)
    }


def _pick(obj: Any, *names: str, default=None):
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return default


def _to_iso(value: Any):
    return value.isoformat() if hasattr(value, "isoformat") else value


# --- serializers --------------------------------------------------------------
def _serialize_message(obj: Model) -> Dict[str, Any]:
    return {
        "id": _pick(obj, "id", "pk"),
        "source": _pick(obj, "source", "channel", "platform"),
        "sender": _pick(obj, "from_name", "sender", "from_address", "author"),
        "subject": _pick(obj, "subject", "title"),
        "summary": _pick(obj, "summary", "abstract", "preview"),
        "priority": _pick(obj, "priority", "importance", "rank"),
        "time": _to_iso(_pick(obj, "received_at", "created_at", "timestamp", "date")),
    }


def _serialize_action(obj: Model) -> Dict[str, Any]:
    return {
        "id": _pick(obj, "id", "pk"),
        "message_id": _pick(obj, "message_id", "message_pk", "message_id_id"),
        "text": _pick(obj, "text", "title", "description"),
        "due": _to_iso(_pick(obj, "due_at", "deadline", "due")),
        "status": _pick(obj, "status", "state"),
    }


# --- queries ------------------------------------------------------------------
def _order_by_recent(qs, ModelClass: type[Model]):
    names = _field_names(ModelClass)
    for field in ("received_at", "created_at", "timestamp", "date", "id"):
        if field in names:
            return qs.order_by(f"-{field}")
    return qs


def _filter_messages(qs, ModelClass: type[Model], params) -> Iterable[Model]:
    names = _field_names(ModelClass)

    source = params.get("source")
    priority = params.get("priority")
    qtext = params.get("q")

    if source and "source" in names:
        qs = qs.filter(source__iexact=source)

    if priority:
        for field in ("priority", "importance", "rank"):
            if field in names:
                qs = qs.filter(**{f"{field}__iexact": priority})
                break

    if qtext:
        q = Q()
        for field in ("subject", "sender", "from_name", "summary", "preview", "body"):
            if field in names:
                q |= Q(**{f"{field}__icontains": qtext})
        if q:
            qs = qs.filter(q)

    return _order_by_recent(qs, ModelClass)


# --- endpoints ----------------------------------------------------------------
def messages_list(request):
    """
    GET /focusflow/api/messages/?page=1&page_size=20&source=email&priority=urgent&q=onboarding
    """
    Message = _get_model("Message", "InboxItem", "EmailMessage")
    if Message is None:
        # graceful mock so the UI works before models are wired
        sample = [
            {
                "id": 1,
                "source": "email",
                "sender": "demo@example.com",
                "subject": "Welcome to FocusFlow",
                "summary": "This is a mock record. Paste your models.py to enable DB data.",
                "priority": "action",
                "time": "2025-10-05T10:00:00Z",
            }
        ]
        return JsonResponse(
            {"results": sample, "count": 1, "num_pages": 1, "page": 1, "source": "mock"}
        )

    qs = Message.objects.all()
    qs = _filter_messages(qs, Message, request.GET)

    page = int(request.GET.get("page", 1))
    page_size = min(max(int(request.GET.get("page_size", 20)), 1), 100)

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    data = [_serialize_message(o) for o in page_obj.object_list]
    return JsonResponse(
        {
            "results": data,
            "count": paginator.count,
            "num_pages": paginator.num_pages,
            "page": page_obj.number,
            "source": "db",
        }
    )


def message_detail(request, pk: int):
    """
    GET /focusflow/api/messages/<pk>/
    Includes related action items if the relationship exists.
    """
    Message = _get_model("Message", "InboxItem", "EmailMessage")
    if Message is None:
        raise Http404("Message model not found. Paste your models.py so I can wire it up.")

    obj = get_object_or_404(Message, pk=pk)
    payload = _serialize_message(obj)

    # try common related names for action items
    actions: list[Dict[str, Any]] = []
    for rel_name in ("actions", "action_items", "tasks"):
        if hasattr(obj, rel_name):
            related = getattr(obj, rel_name).all()
            actions = [_serialize_action(a) for a in related]
            break

    payload["actions"] = actions
    return JsonResponse(payload)


def actions_list(request):
    """
    GET /focusflow/api/actions/?status=open&q=contract
    """
    Action = _get_model("ActionItem", "Action", "Task")
    if Action is None:
        # mock
        sample = [
            {
                "id": 101,
                "message_id": 1,
                "text": "Reply to onboarding email",
                "due": None,
                "status": "open",
            }
        ]
        return JsonResponse({"results": sample, "count": 1, "source": "mock"})

    names = _field_names(Action)
    qs = Action.objects.all()

    status = request.GET.get("status")
    qtext = request.GET.get("q")

    if status and "status" in names:
        qs = qs.filter(status__iexact=status)
    if qtext:
        q = Q()
        for field in ("text", "title", "description"):
            if field in names:
                q |= Q(**{f"{field}__icontains": qtext})
        if q:
            qs = qs.filter(q)

    page = int(request.GET.get("page", 1))
    page_size = min(max(int(request.GET.get("page_size", 20)), 1), 100)
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    data = [_serialize_action(o) for o in page_obj.object_list]
    return JsonResponse(
        {
            "results": data,
            "count": paginator.count,
            "num_pages": paginator.num_pages,
            "page": page_obj.number,
            "source": "db",
        }
    )