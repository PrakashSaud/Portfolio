from django.urls import path
from . import views

app_name = "focusflow"

urlpatterns = [
    path("", views.home, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("gmail/connect/", views.connect_gmail, name="connect_gmail"),
    path("gmail/auth/", views.gmail_auth, name="gmail_auth"),         # placeholder
    path("gmail/callback/", views.gmail_callback, name="gmail_callback"),  # placeholder
]