from __future__ import annotations

from typing import List


def classify_ticket(text: str) -> dict:
    t = (text or "").lower()

    if any(k in t for k in ["billing", "invoice", "refund", "charge", "payment"]):
        tag = "billing"
    elif any(k in t for k in ["integration", "api", "webhook", "sync"]):
        tag = "integration"
    elif any(k in t for k in ["login", "access", "password", "2fa", "auth"]):
        tag = "access"
    elif any(k in t for k in ["slow", "latency", "performance", "timeout"]):
        tag = "performance"
    elif any(k in t for k in ["bug", "error", "issue", "broken", "crash", "500"]):
        tag = "bug"
    else:
        tag = "general"

    if any(k in t for k in ["angry", "frustrated", "upset", "terrible", "unacceptable"]):
        sentiment = "negative"
    elif any(k in t for k in ["thanks", "appreciate", "great", "love"]):
        sentiment = "positive"
    else:
        sentiment = "neutral"

    if any(k in t for k in ["urgent", "asap", "down", "outage", "can't", "cannot", "blocked"]):
        urgency = "high"
    elif any(k in t for k in ["soon", "today", "quick"]):
        urgency = "medium"
    else:
        urgency = "low"

    return {"tag": tag, "sentiment": sentiment, "urgency": urgency}


def suggested_macros(tag: str) -> List[str]:
    macros = {
        "billing": [
            "Thanks for flagging this. Can you share the invoice ID and the last 4 digits of the card used?",
            "I can look into the charge right away. What plan are you on and when did you notice the issue?",
        ],
        "integration": [
            "Got it. Which integration (API/webhook) is failing and when did it start?",
            "Can you share the request ID or payload so I can trace it on our side?",
        ],
        "access": [
            "Thanks. Are you seeing an invalid password error or a 2FA issue?",
            "Please confirm the email and whether this happens on all devices.",
        ],
        "performance": [
            "Sorry about the slowdown. Which page or action feels slow, and roughly when did it start?",
            "Can you share browser + region so we can check latency?",
        ],
        "bug": [
            "Thanks for the report. Can you share steps to reproduce and the exact error message?",
            "Which browser/device were you using when this happened?",
        ],
        "general": [
            "Thanks for reaching out. Can you share more details so we can help quickly?",
        ],
    }
    return macros.get(tag, macros["general"])
