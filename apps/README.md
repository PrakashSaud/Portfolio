# FocusFlow

**FocusFlow** is a unified smart inbox built as a Django app (inside your portfolio project).  
It consolidates messages from multiple channels, uses AI to prioritize and summarize them, and extracts actionable tasks — helping users focus on what matters.

---

## 🎯 Vision & Goals

- **Unified Inbox**: Merge emails, Slack/Teams, WhatsApp, etc. into one timeline per workspace  
- **AI Prioritization & Summaries**: Automatically label messages as Urgent / Action / FYI / Spam, and generate readable summaries  
- **Action Extraction & Task Management**: Create actionable tasks from messages (deadlines, follow-ups, assignments)  
- **Focus Mode**: Filter out noise — only critical messages surface  
- **Analytics & Insights**: Track time spent by channel, most active contacts, communication trends  
- **Monetization Strategy**:  
  - *Free plan*: basic email integration + daily summary  
  - *Pro plan*: multiple integrations, focus mode, advanced AI  
  - *Enterprise*: team insights, dashboards, company-level metrics  

---

## 🧱 Architecture & Models Overview

Key models defined (in `models.py`):

- **Workspace**, **WorkspaceMember** — multi-tenant support  
- **Integration**, **Stream** — represent connected channels (Gmail, Slack, etc.)  
- **Conversation**, **Message** — store thread-level and individual message data  
- **AIAnnotation** — generic annotation entity (summary, priority, entities) via GenericForeignKey  
- **Task** — actionable items extracted from messages/conversations  

---

## 🚀 Getting Started (Development)

### Prerequisites

- Python ≥ 3.9  
- Django (your project’s version)  
- Tailwind / your existing front-end stack  
- (Later) Hugging Face, OAuth credentials for Gmail, etc.

### Setup

1. **Add app to INSTALLED_APPS** (if not already):
   ```python
   INSTALLED_APPS += ["apps.focusflow"]