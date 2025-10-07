# apps/focusflow/api.py
from __future__ import annotations

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404

from .models import Message, Task, Conversation, AIAnnotation


# --- helpers -----------------------------------------------------------------
def _paginate(request, queryset, serializer):
    """Universal pagination helper for JSON APIs."""
    page = int(request.GET.get("page", 1))
    page_size = min(max(int(request.GET.get("page_size", 20)), 1), 100)

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    data = [serializer(obj) for obj in page_obj.object_list]

    return JsonResponse(
        {
            "results": data,
            "count": paginator.count,
            "num_pages": paginator.num_pages,
            "page": page_obj.number,
        }
    )


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


# --- serializers --------------------------------------------------------------
def _serialize_message(m: Message):
    return {
        "id": m.id,
        "conversation_id": m.conversation_id,
        "stream": getattr(m.stream, "name", None),
        "sender": getattr(m.sender, "display_name", None),
        "sent_at": _iso(m.sent_at),
        "text": m.text[:400] if m.text else None,
        "is_read": m.is_read,
        "external_url": m.external_url or "",
        "created_at": _iso(m.created_at),
    }


def _serialize_task(t: Task):
    return {
        "id": t.id,
        "title": t.title,
        "status": t.status,
        "due_at": _iso(t.due_at),
        "confidence": t.confidence,
        "assignee": getattr(t.assignee, "username", None),
        "workspace": getattr(t.workspace, "name", None),
    }


def _serialize_conversation(c: Conversation):
    return {
        "id": c.id,
        "workspace": getattr(c.workspace, "name", None),
        "stream": getattr(c.stream, "name", None),
        "subject": c.subject,
        "priority": c.priority,
        "state": c.state,
        "last_message_at": _iso(c.last_message_at),
        "unread_count": c.unread_count,
    }


def _serialize_annotation(a: AIAnnotation):
    return {
        "id": a.id,
        "workspace": getattr(a.workspace, "name", None),
        "kind": a.kind,
        "content_text": a.content_text,
        "score": a.score,
        "target_type": a.target_content_type.model,
        "target_id": a.target_object_id,
        "created_at": _iso(a.created_at),
    }


# --- endpoints ----------------------------------------------------------------
def messages_list(request):
    """GET /focusflow/api/messages/"""
    qs = Message.objects.select_related("sender", "stream", "conversation")

    # filters
    conversation_id = request.GET.get("conversation_id")
    stream_id = request.GET.get("stream_id")
    qtext = request.GET.get("q")

    if conversation_id:
        qs = qs.filter(conversation_id=conversation_id)
    if stream_id:
        qs = qs.filter(stream_id=stream_id)
    if qtext:
        qs = qs.filter(Q(text__icontains=qtext) | Q(html__icontains=qtext))

    qs = qs.order_by("-sent_at")
    return _paginate(request, qs, _serialize_message)


def message_detail(request, pk: int):
    """GET /focusflow/api/messages/<id>/"""
    obj = get_object_or_404(Message.objects.select_related("sender", "conversation"), pk=pk)
    payload = _serialize_message(obj)

    # AI annotations linked to this message
    annotations = AIAnnotation.objects.filter(
        target_content_type__model="message", target_object_id=obj.id
    )
    payload["annotations"] = [_serialize_annotation(a) for a in annotations]
    return JsonResponse(payload)


def actions_list(request):
    """GET /focusflow/api/actions/"""
    qs = Task.objects.select_related("workspace", "assignee")
    status = request.GET.get("status")
    qtext = request.GET.get("q")

    if status:
        qs = qs.filter(status=status)
    if qtext:
        qs = qs.filter(title__icontains=qtext)

    qs = qs.order_by("-created_at")
    return _paginate(request, qs, _serialize_task)


def conversations_list(request):
    """GET /focusflow/api/conversations/"""
    qs = Conversation.objects.select_related("workspace", "stream")

    priority = request.GET.get("priority")
    state = request.GET.get("state")
    qtext = request.GET.get("q")

    if priority:
        qs = qs.filter(priority=priority)
    if state:
        qs = qs.filter(state=state)
    if qtext:
        qs = qs.filter(Q(subject__icontains=qtext))

    qs = qs.order_by("-last_message_at")
    return _paginate(request, qs, _serialize_conversation)


def conversation_detail(request, pk: int):
    """GET /focusflow/api/conversations/<id>/"""
    c = get_object_or_404(Conversation.objects.select_related("workspace", "stream"), pk=pk)
    data = _serialize_conversation(c)

    messages = Message.objects.filter(conversation=c).select_related("sender").order_by("-sent_at")[:50]
    data["messages"] = [_serialize_message(m) for m in messages]

    annotations = AIAnnotation.objects.filter(
        target_content_type__model="conversation", target_object_id=c.id
    )
    data["annotations"] = [_serialize_annotation(a) for a in annotations]

    return JsonResponse(data)

def annotations_list(request):
    """
    GET /focusflow/api/annotations/?kind=summary
    Returns AI annotations (summaries, priorities, etc.)
    """
    qs = AIAnnotation.objects.select_related("workspace")
    kind = request.GET.get("kind")
    if kind:
        qs = qs.filter(kind=kind)

    page = int(request.GET.get("page", 1))
    page_size = min(max(int(request.GET.get("page_size", 20)), 1), 100)

    from django.core.paginator import Paginator
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    def _serialize(a):
        return {
            "id": a.id,
            "workspace": getattr(a.workspace, "name", None),
            "kind": a.kind,
            "content_text": a.content_text,
            "score": a.score,
            "created_at": a.created_at.isoformat(),
            "target_type": a.target_content_type.model,
            "target_id": a.target_object_id,
        }

    data = [_serialize(a) for a in page_obj.object_list]
    return JsonResponse(
        {
            "results": data,
            "count": paginator.count,
            "num_pages": paginator.num_pages,
            "page": page_obj.number,
        }
    )