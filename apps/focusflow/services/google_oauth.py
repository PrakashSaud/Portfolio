# portfolio_web/apps/focusflow/services/google_oauth.py
from __future__ import annotations

import os
import requests
from urllib.parse import urlencode

# Google OAuth 2.0 endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/gmail/v1/users/me/profile"
GOOGLE_MESSAGES_URL = "https://www.googleapis.com/gmail/v1/users/me/messages"


def build_auth_url() -> str:
    """
    Generate Google's OAuth URL to begin user authorization.
    """
    params = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """
    Exchange authorization code for access & refresh tokens.
    """
    data = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "grant_type": "authorization_code",
    }
    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    if response.status_code != 200:
        print("Token exchange failed:", response.text)
    return response.json()


def get_gmail_profile_email(access_token: str) -> str | None:
    """
    Fetch the authenticated user's primary Gmail address.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(GOOGLE_USERINFO_URL, headers=headers)
    if res.status_code == 200:
        return res.json().get("emailAddress")
    print("Failed to fetch Gmail profile:", res.text)
    return None


def list_recent_message_headers(access_token: str, max_results: int = 5):
    """
    Retrieve a few recent Gmail message headers for dashboard preview.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"maxResults": max_results, "labelIds": "INBOX"}
    res = requests.get(GOOGLE_MESSAGES_URL, headers=headers, params=params)
    if res.status_code != 200:
        print("Failed to list messages:", res.text)
        return []

    data = res.json()
    messages = data.get("messages", [])
    summaries = []

    for msg in messages:
        msg_id = msg.get("id")
        detail = requests.get(f"{GOOGLE_MESSAGES_URL}/{msg_id}", headers=headers, params={"format": "metadata"})
        if detail.status_code == 200:
            payload = detail.json()
            headers_data = payload.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers_data if h["name"] == "Subject"), "(no subject)")
            sender = next((h["value"] for h in headers_data if h["name"] == "From"), "(unknown sender)")
            date = next((h["value"] for h in headers_data if h["name"] == "Date"), "")
            summaries.append({
                "source": "email",
                "sender": sender,
                "subject": subject,
                "time": date,
                "summary": "Fetched from Gmail API.",
                "actions": [],
            })
    return summaries