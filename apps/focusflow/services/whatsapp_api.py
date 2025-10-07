# apps/focusflow/services/whatsapp_api.py
from __future__ import annotations
import random
from datetime import datetime, timedelta

def connect_whatsapp(account_label: str = "My WhatsApp") -> dict:
    """
    Simulate WhatsApp connection. Later, this will use Meta's Graph API.
    """
    return {
        "provider": "whatsapp",
        "account_label": account_label,
        "status": "active",
        "connected_at": datetime.now().isoformat(),
    }

def list_recent_messages(max_results: int = 5):
    """
    Mock WhatsApp messages for testing dashboard visualization.
    """
    contacts = ["Client A", "Support Team", "Mom", "Best Friend", "Manager"]
    messages = []
    now = datetime.now()

    for i in range(max_results):
        sender = random.choice(contacts)
        messages.append({
            "source": "whatsapp",
            "sender": sender,
            "subject": f"New message from {sender}",
            "summary": f"Quick note from {sender} — hope your day’s going well!",
            "time": (now - timedelta(minutes=i*10)).strftime("%Y-%m-%d %H:%M:%S"),
            "actions": [],
        })
    return messages