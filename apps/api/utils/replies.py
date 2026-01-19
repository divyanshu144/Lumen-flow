from apps.api.data.service_catalog import SERVICE_CATALOG

def detect_topic(message: str) -> str:
    text = (message or "").lower()
    for svc in SERVICE_CATALOG["services"]:
        if any(k in text for k in svc["keywords"]):
            return svc["name"]
    return "General"

def build_reply(message: str) -> str:
    topic = detect_topic(message)
    services = SERVICE_CATALOG["services"]

    if "service" in (message or "").lower() or "services" in (message or "").lower():
        bullets = "\n".join([f"- **{s['name']}** — {s['description']}" for s in services])
        return (
            "Here’s what we can help with:\n\n"
            f"{bullets}\n\n"
            "If you tell me which CRM you use and what you’re trying to achieve, I’ll suggest the best next step."
        )

    if any(x in (message or "").lower() for x in ["price", "pricing", "cost", "quote"]):
        return (
            f"{SERVICE_CATALOG['pricing_note']}\n\n"
            "Quick questions:\n"
            "1) Which CRM (HubSpot/Salesforce/etc.)?\n"
            "2) What needs integrating (WhatsApp, forms, website, billing)?\n"
            "3) Rough timeline (this week / this month)?"
        )

    # topic-based answer
    match = next((s for s in services if s["name"] == topic), None)
    if match:
        return (
            f"Got it — sounds like **{match['name']}**.\n\n"
            f"{match['description']}\n\n"
            "Tell me your CRM + what tools you want connected, and I’ll outline a clean approach."
        )

    return "Got it. Tell me what you’re trying to do (CRM, automation, integrations, or support) and I’ll guide you."