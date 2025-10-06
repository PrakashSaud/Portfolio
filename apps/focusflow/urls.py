# apps/focusflow/urls.py
from django.urls import path
from . import views
from . import api  # <-- new

app_name = "focusflow"

urlpatterns = [
    # pages
    path("", views.home, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("gmail/connect/", views.connect_gmail, name="connect_gmail"),
    path("gmail/auth/", views.gmail_auth, name="gmail_auth"),
    path("gmail/callback/", views.gmail_callback, name="gmail_callback"),

    # api
    path("api/messages/", api.messages_list, name="api_messages_list"),
    path("api/messages/<int:pk>/", api.message_detail, name="api_message_detail"),
    path("api/actions/", api.actions_list, name="api_actions_list"),
]