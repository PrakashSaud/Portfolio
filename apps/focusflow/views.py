from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from .services.whatsapp_api import connect_whatsapp, list_recent_messages

import os

from .services.google_oauth import (
    build_auth_url,
    exchange_code_for_token,
    get_gmail_profile_email,
    list_recent_message_headers,
)

# Optional DB persistence when user is authenticated
try:
    from .models import Workspace, Integration
except Exception:
    Workspace = None
    Integration = None

User = get_user_model()


# -----------------------
# Pages
# -----------------------

def home(request):
    return render(request, "focusflow/home.html")


def dashboard(request):
    # Combine Gmail and WhatsApp summaries
    summaries = []

    gmail_summaries = request.session.get("gmail_summaries", [])
    whatsapp_summaries = request.session.get("whatsapp_summaries", [])

    if gmail_summaries:
        summaries.extend(gmail_summaries)
    if whatsapp_summaries:
        summaries.extend(whatsapp_summaries)

    # If still empty, fall back to placeholder mock cards
    if not summaries:
        summaries = [
            {
                "source": "email",
                "sender": "HR Team <hr@company.com>",
                "time": "Today, 10:42 AM",
                "subject": "Onboarding Schedule & Tasks",
                "summary": "Here’s your checklist for next week: complete paperwork, schedule laptop pickup, and read the handbook.",
                "actions": ["Sign NDA", "Schedule IT setup", "Confirm start date"],
            },
            {
                "source": "slack",
                "sender": "Boss (Slack)",
                "time": "Today, 9:15 AM",
                "subject": "Client review call rescheduled",
                "summary": "The review call moved to Friday 2pm ET. Prep slides on metrics and risks.",
                "actions": ["Update deck", "Share agenda by Thu EOD"],
            },
        ]

    return render(request, "focusflow/dashboard.html", {"summaries": summaries})

def analytics(request):
    return render(request, "focusflow/analytics.html")


def integrations(request):
    """
    Integrations screen:
      - Shows Gmail connection status using session (back-compat).
      - Builds a DB-driven list of all integrations owned by the signed-in user.
      - Auto-creates default placeholders (Gmail, Slack, Teams, WhatsApp) if user has none.
    """
    # Back-compat (your current template can keep using these safely)
    session_connected = bool(request.session.get("gmail_access_token"))
    account_label = request.session.get("gmail_account_label")  # email

    db_integration = None
    user_integrations = []

    # Provider metadata (used for icons + labels)
    provider_meta = {
        "gmail": {
            "label": "Gmail",
            "icon": "focusflow/img/gmail-icon.svg",
            "connect_url": reverse("focusflow:gmail_auth"),
            "disconnect_url": reverse("focusflow:gmail_disconnect"),
            "coming_soon": False,
        },
        "slack": {
            "label": "Slack",
            "icon": "focusflow/img/slack-icon.svg",
            "connect_url": None,
            "disconnect_url": None,
            "coming_soon": True,
        },
        "teams": {
            "label": "Microsoft Teams",
            "icon": None,
            "connect_url": None,
            "disconnect_url": None,
            "coming_soon": True,
        },
        "whatsapp": {
            "label": "WhatsApp",
            "icon": None,
            "connect_url": None,
            "disconnect_url": None,
            "coming_soon": True,
        },
    }

    # Only handle DB logic if logged in and model is available
    if request.user.is_authenticated and Integration is not None and Workspace is not None:
        # Ensure a workspace exists
        ws, _ = Workspace.objects.get_or_create(
            owner=request.user,
            defaults={
                "name": f"{request.user.username}'s Workspace",
                "slug": slugify(f"{request.user.username}-ws"),
            },
        )

        # Auto-create default integrations if none exist
        if not Integration.objects.filter(workspace=ws).exists():
            for provider, meta in provider_meta.items():
                Integration.objects.create(
                    workspace=ws,
                    provider=provider,
                    account_label=f"{meta['label']} Account",
                    status="disconnected" if not meta.get("coming_soon") else "paused",
                    sync_status="idle",
                )

        # Get most recent Gmail integration for legacy display
        db_integration = (
            Integration.objects.filter(
                provider="gmail",
                workspace=ws,
                status__in=["active", "paused", "error", "disconnected"],
            )
            .order_by("-created_at")
            .first()
        )

        # Full list for template loop
        qs = (
            Integration.objects.filter(workspace=ws)
            .order_by("provider", "account_label")
        )
        for integ in qs:
            meta = provider_meta.get(integ.provider, {})
            user_integrations.append(
                {
                    "id": integ.id,
                    "provider": integ.provider,
                    "provider_label": meta.get("label") or integ.get_provider_display(),
                    "icon": meta.get("icon"),
                    "account_label": integ.account_label,
                    "status": integ.status,
                    "status_display": integ.get_status_display() if hasattr(integ, "get_status_display") else integ.status,
                    "workspace": integ.workspace.name if integ.workspace_id else "",
                    "connect_url": meta.get("connect_url"),
                    "disconnect_url": meta.get("disconnect_url"),
                    "coming_soon": meta.get("coming_soon", False),
                }
            )

    ctx = {
        "session_connected": session_connected,
        "account_label": account_label,
        "db_integration": db_integration,
        "integrations": user_integrations,
        "provider_meta": provider_meta,
    }
    return render(request, "focusflow/integrations.html", ctx)

def connect_gmail(request):
    return render(request, "focusflow/connect_gmail.html")


# -----------------------
# Gmail OAuth
# -----------------------

def gmail_auth(request):
    # Ensure env is loaded in settings (load_dotenv), otherwise envs might be None
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not client_id or not redirect_uri:
        messages.error(request, "Google OAuth is not configured. Check GOOGLE_CLIENT_ID / GOOGLE_REDIRECT_URI.")
        return redirect("focusflow:integrations")

    auth_url = build_auth_url()
    # Debug — visible in terminal
    print("DEBUG OAuth →", auth_url)
    return redirect(auth_url)


def gmail_callback(request):
    if request.GET.get("error"):
        messages.error(request, f"Google OAuth error: {request.GET.get('error')}")
        return redirect("focusflow:integrations")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "Authorization code missing. Try connecting again.")
        return redirect("focusflow:integrations")

    token_data = exchange_code_for_token(code)
    print("DEBUG Token response:", token_data)

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    if not access_token:
        messages.error(request, "Failed to retrieve access token. Check Google Cloud credentials/redirect URI.")
        return redirect("focusflow:integrations")

    # Get the primary Gmail address (for display + Integration.account_label)
    email = get_gmail_profile_email(access_token) or "unknown@example.com"

    # Save tokens to session for local testing
    request.session["gmail_access_token"] = access_token
    if refresh_token:
        request.session["gmail_refresh_token"] = refresh_token
    request.session["gmail_account_label"] = email

    # If authenticated user exists, persist an Integration row for visibility
    if request.user.is_authenticated and Workspace is not None and Integration is not None:
        ws = Workspace.objects.filter(owner=request.user).order_by("created_at").first()
        if ws is None:
            # create a lightweight personal workspace
            ws = Workspace.objects.create(
                name=f"{request.user.username}'s Workspace",
                slug=slugify(f"{request.user.username}-ws"),
                owner=request.user,
            )
        integ, created = Integration.objects.get_or_create(
            workspace=ws,
            provider="gmail",
            account_label=email,
            defaults={"status": "active", "scopes_json": ["gmail.readonly"], "sync_status": "idle"},
        )
        if not created:
            # Mark it active again if previously disconnected
            integ.status = "active"
            integ.save(update_fields=["status"])

    # Prime the dashboard with a few real messages
    summaries = list_recent_message_headers(access_token, max_results=5)
    request.session["gmail_summaries"] = summaries

    messages.success(request, f"Gmail connected: {email}. Retrieved {len(summaries)} messages.")
    return redirect("focusflow:integrations")


def gmail_disconnect(request):
    # Clear session tokens
    for k in ("gmail_access_token", "gmail_refresh_token", "gmail_account_label", "gmail_summaries"):
        request.session.pop(k, None)

    # Update DB Integration status if present
    if request.user.is_authenticated and Integration is not None:
        Integration.objects.filter(
            provider="gmail",
            workspace__owner=request.user,
        ).update(status="disconnected")

    messages.info(request, "Gmail disconnected.")
    return redirect("focusflow:integrations")

    # -----------------------
# WhatsApp Integration
# -----------------------

def whatsapp_connect(request):
    """
    Simulates connecting a WhatsApp account.
    """
    data = connect_whatsapp(account_label="Demo WhatsApp")
    request.session["whatsapp_connected"] = True
    request.session["whatsapp_account_label"] = data["account_label"]

    # Store messages in session for dashboard preview
    request.session["whatsapp_summaries"] = list_recent_messages(5)

    # Update Integration model if available
    if request.user.is_authenticated and Integration is not None and Workspace is not None:
        ws, _ = Workspace.objects.get_or_create(
            owner=request.user,
            defaults={
                "name": f"{request.user.username}'s Workspace",
                "slug": slugify(f"{request.user.username}-ws"),
            },
        )
        integ, created = Integration.objects.get_or_create(
            workspace=ws,
            provider="whatsapp",
            account_label=data["account_label"],
            defaults={"status": "active", "sync_status": "idle"},
        )
        if not created:
            integ.status = "active"
            integ.save(update_fields=["status"])

    messages.success(request, f"✅ WhatsApp connected as {data['account_label']}")
    return redirect("focusflow:integrations")


def whatsapp_disconnect(request):
    """
    Disconnect WhatsApp (session + DB state).
    """
    for key in ("whatsapp_connected", "whatsapp_account_label", "whatsapp_summaries"):
        request.session.pop(key, None)

    if request.user.is_authenticated and Integration is not None:
        Integration.objects.filter(
            provider="whatsapp",
            workspace__owner=request.user,
        ).update(status="disconnected")

    messages.info(request, "🔌 WhatsApp disconnected.")
    return redirect("focusflow:integrations")