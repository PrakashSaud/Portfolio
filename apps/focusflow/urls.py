# apps/focusflow/urls.py
from django.urls import path
from . import views, api

app_name = "focusflow"

urlpatterns = [
    # ---------------------------
    # Frontend pages
    # ---------------------------
    path("", views.home, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("analytics/", views.analytics, name="analytics"),
    path("integrations/", views.integrations, name="integrations"),

    # Gmail connection workflow
    path("gmail/connect/", views.connect_gmail, name="connect_gmail"),
    path("gmail/auth/", views.gmail_auth, name="gmail_auth"),
    path("gmail/callback/", views.gmail_callback, name="gmail_callback"),
    path("gmail/disconnect/", views.gmail_disconnect, name="gmail_disconnect"),

    # WhatsApp connection workflow
    path("whatsapp/connect/", views.whatsapp_connect, name="whatsapp_connect"),
    path("whatsapp/disconnect/", views.whatsapp_disconnect, name="whatsapp_disconnect"),

    # ---------------------------
    # Backend API endpoints
    # ---------------------------

    # Conversations
    path("api/conversations/", api.conversations_list, name="api_conversations_list"),
    path("api/conversations/<int:pk>/", api.conversation_detail, name="api_conversation_detail"),

    # Messages
    path("api/messages/", api.messages_list, name="api_messages_list"),
    path("api/messages/<int:pk>/", api.message_detail, name="api_message_detail"),

    # AI Annotations (summaries, priorities, etc.)
    path("api/annotations/", api.annotations_list, name="api_annotations_list"),

    # Tasks / Action Items
    path("api/actions/", api.actions_list, name="api_actions_list"),
]