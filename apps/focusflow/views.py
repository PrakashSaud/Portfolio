from django.shortcuts import render, redirect

# HOME / landing
def home(request):
    return render(request, "focusflow/home.html")

# Dashboard (uses summaries when available; empty state otherwise)
def dashboard(request):
    # placeholder mock data for visual testing; remove when you wire real data
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

# Connect page
def connect_gmail(request):
    return render(request, "focusflow/connect_gmail.html")

# OAuth placeholders (next steps)
def gmail_auth(request):
    return redirect("focusflow:dashboard")

def gmail_callback(request):
    return redirect("focusflow:dashboard")