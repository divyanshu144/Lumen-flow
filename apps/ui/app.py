import os
from pathlib import Path

import httpx
import pandas as pd
import streamlit as st

# Use env var in docker; defaults to docker service name
API_URL = os.getenv("API_URL", "http://api:8000")
# If running UI locally (outside docker), set:
# API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="ClientOps AI", layout="wide")


def load_css():
    css_path = Path(__file__).with_name("styles.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_css()


try:
    from apps.api.data.service_catalog import SERVICE_CATALOG
except Exception:
    SERVICE_CATALOG = {
        "services": [
            {
                "name": "CRM + Data Setup",
                "description": "CRM implementation + data model, pipelines, integrations, dashboards.",
                "keywords": ["crm", "pipeline", "dashboard", "data"],
            },
            {
                "name": "CRM Integrations",
                "description": "Connect CRM with WhatsApp, email, forms, billing, and internal tools.",
                "keywords": ["integration", "whatsapp", "email", "forms", "billing"],
            },
            {
                "name": "Automation & Workflows",
                "description": "Automated lead routing, follow-ups, ticket triage, and reminders.",
                "keywords": ["automation", "workflow", "follow-up", "routing"],
            },
            {
                "name": "Support / Troubleshooting",
                "description": "Diagnose issues, fix bugs, and improve reliability & monitoring.",
                "keywords": ["bug", "issue", "error", "support", "help"],
            },
        ],
        "pricing_note": "Pricing is tailored to your CRM stack and integration scope.",
    }


# ---- helpers ----

def safe_get_json(url: str):
    try:
        r = httpx.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error calling {url}: {e}")
        return None


def safe_post_json(url: str, payload: dict):
    try:
        r = httpx.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error calling {url}: {e}")
        return None


def safe_patch_json(url: str, payload: dict):
    try:
        r = httpx.patch(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error calling {url}: {e}")
        return None


def detect_topic(text: str) -> dict | None:
    text_l = (text or "").lower()
    for svc in SERVICE_CATALOG.get("services", []):
        if any(k in text_l for k in svc.get("keywords", [])):
            return svc
    return None


def build_routing(intent: str | None) -> str:
    if intent == "lead":
        return "Sales"
    if intent == "ticket":
        return "Support"
    return "General"


def build_followup_preview(intent: str | None, topic: dict | None, payload: dict) -> tuple[str, str]:
    name = payload.get("name") or "there"
    crm = payload.get("crm") or "your CRM"
    goal = payload.get("goal") or "your workflow"
    timeline = payload.get("timeline") or "soon"

    if intent == "ticket":
        subject = "We received your support request"
        body = (
            f"Hi {name},\n\n"
            "Thanks for reporting the issue. To speed this up, could you share:\n"
            "1) device/browser\n2) exact error message\n3) steps to reproduce\n\n"
            "We will jump on it right away.\n\nBest,\nClientOps AI"
        )
        return subject, body

    if intent == "lead":
        topic_name = (topic or {}).get("name", "ClientOps")
        subject = f"Next steps for {topic_name}"
        body = (
            f"Hi {name},\n\n"
            f"Thanks for sharing your goals around {goal}.\n"
            f"We can connect {crm} and streamline the process within {timeline}.\n\n"
            "If you are open to it, I can propose a short plan and timeline.\n\n"
            "Best,\nClientOps AI"
        )
        return subject, body

    subject = "Quick follow-up"
    body = (
        f"Hi {name},\n\n"
        "Thanks for reaching out. Tell me a bit more about your CRM and goals and I will outline next steps.\n\n"
        "Best,\nClientOps AI"
    )
    return subject, body


def compose_message_from_form(payload: dict) -> str:
    bits = []
    if payload.get("goal"):
        bits.append(payload["goal"])
    if payload.get("crm"):
        bits.append(f"CRM: {payload['crm']}")
    if payload.get("timeline"):
        bits.append(f"Timeline: {payload['timeline']}")
    if payload.get("company"):
        bits.append(f"Company: {payload['company']}")
    if payload.get("name"):
        bits.append(f"Name: {payload['name']}")
    return ". ".join(bits) if bits else "Looking for help with CRM and automation."


PAGES = ["Overview", "Chat", "Admin"]
query_page = st.query_params.get("page", [None])[0]
default_index = PAGES.index(query_page) if query_page in PAGES else 0

# ---- sidebar navigation ----
with st.sidebar:
    st.markdown("<div class='sidebar-title'>Lumen Core</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sidebar-sub'>ClientOps engine for lead intent, drafts, and approvals.</div>",
        unsafe_allow_html=True,
    )
    page = st.radio("Navigate", PAGES, index=default_index)
    st.divider()
    st.caption("Environment")
    st.code(API_URL, language="text")


# ---- load shared data ----
contacts = safe_get_json(f"{API_URL}/admin/contacts")
leads = safe_get_json(f"{API_URL}/admin/leads")
tickets = safe_get_json(f"{API_URL}/admin/tickets")


def to_df(data):
    return pd.DataFrame(data) if data else pd.DataFrame([])


df_contacts = to_df(contacts)
df_leads = to_df(leads)
df_tickets = to_df(tickets)


if page == "Overview":
    left, right = st.columns([3, 2])
    with left:
        st.markdown(
            """
            <div class="hero">
                <div class="pill">ClientOps OS</div>
                <h1 class="hero-title">Turn chat intent into revenue-ready workflows.</h1>
                <p class="hero-sub">Lumen detects lead intent, drafts follow-ups, and keeps humans in the loop before anything is sent.</p>
                <div class="cta-row">
                    <a class="cta-primary" href="?page=Chat">Try live demo</a>
                    <a class="cta-secondary" href="#metrics">See metrics</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<a id='how-it-works'></a>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>How it works</div>", unsafe_allow_html=True)
        h1, h2, h3 = st.columns(3)
        with h1:
            st.markdown(
                "<div class='card'><div class='card-title'>Detect</div>"
                "<div class='card-muted'>Classify intent and route to the right workflow instantly.</div></div>",
                unsafe_allow_html=True,
            )
        with h2:
            st.markdown(
                "<div class='card'><div class='card-title'>Draft</div>"
                "<div class='card-muted'>Generate high-quality follow-ups and suggested actions.</div></div>",
                unsafe_allow_html=True,
            )
        with h3:
            st.markdown(
                "<div class='card'><div class='card-title'>Approve</div>"
                "<div class='card-muted'>Human-in-the-loop review before sending or advancing.</div></div>",
                unsafe_allow_html=True,
            )

    with right:
        st.markdown(
            """
            <div class="product-preview">
                <div class="card-title">Product Preview</div>
                <div class="preview-step">
                    <span class="preview-dot"></span>
                    Lead detected from chat message
                </div>
                <div class="preview-step">
                    <span class="preview-dot amber"></span>
                    Draft created and queued for review
                </div>
                <div class="preview-step">
                    <span class="preview-dot green"></span>
                    Approve + send follow-up
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<a id='metrics'></a>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Metrics</div>", unsafe_allow_html=True)

    metrics = safe_get_json(f"{API_URL}/admin/metrics") or {}
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            "<div class='card'><div class='card-title'>Contacts</div><div class='card-muted'>Total records</div></div>",
            unsafe_allow_html=True,
        )
        st.metric("", metrics.get("contacts", int(df_contacts.shape[0])))
    with c2:
        st.markdown(
            "<div class='card'><div class='card-title'>Leads</div><div class='card-muted'>Active pipeline</div></div>",
            unsafe_allow_html=True,
        )
        st.metric("", metrics.get("leads", int(df_leads.shape[0])))
    with c3:
        st.markdown(
            "<div class='card'><div class='card-title'>Tickets</div><div class='card-muted'>Support queue</div></div>",
            unsafe_allow_html=True,
        )
        st.metric("", metrics.get("tickets", int(df_tickets.shape[0])))
    with c4:
        st.markdown(
            "<div class='card'><div class='card-title'>Drafts</div><div class='card-muted'>Pending approvals</div></div>",
            unsafe_allow_html=True,
        )
        st.metric("", metrics.get("drafts_pending", 0))

    c5, c6, c7 = st.columns(3)
    with c5:
        st.markdown(
            "<div class='card'><div class='card-title'>Conversations</div><div class='card-muted'>Active sessions</div></div>",
            unsafe_allow_html=True,
        )
        st.metric("", metrics.get("conversations", 0))
    with c6:
        st.markdown(
            "<div class='card'><div class='card-title'>Messages</div><div class='card-muted'>Total logs</div></div>",
            unsafe_allow_html=True,
        )
        st.metric("", metrics.get("messages", 0))
    with c7:
        st.markdown(
            "<div class='card'><div class='card-title'>Avg response</div><div class='card-muted'>Seconds</div></div>",
            unsafe_allow_html=True,
        )
        avg_sec = metrics.get("avg_response_sec")
        st.metric("", f"{avg_sec:.1f}s" if isinstance(avg_sec, (int, float)) else "—")

    st.markdown("<div class='section-title'>Intent distribution</div>", unsafe_allow_html=True)
    intent = safe_get_json(f"{API_URL}/admin/intent") or {"lead": 0, "ticket": 0, "general": 0}
    intent_df = pd.DataFrame(
        [
            {"intent": "lead", "count": intent.get("lead", 0)},
            {"intent": "ticket", "count": intent.get("ticket", 0)},
            {"intent": "general", "count": intent.get("general", 0)},
        ]
    )
    st.bar_chart(intent_df, x="intent", y="count", height=220)

    s1, s2 = st.columns([1, 3])
    with s1:
        if st.button("Seed demo data"):
            res = safe_post_json(f"{API_URL}/admin/seed-demo", {})
            if res is not None:
                st.success("Demo data seeded.")
                st.rerun()
    with s2:
        st.caption("Use demo data to populate metrics and showcase the flow.")

    st.markdown("<div class='section-title'>Proof in the outcomes</div>", unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown(
            "<div class='card-ghost'><div class='card-title'>SaaS onboarding revamp</div>"
            "<div class='card-muted'>Reduced lead response time from 12 hours to 15 minutes and doubled demo bookings.</div></div>",
            unsafe_allow_html=True,
        )
    with p2:
        st.markdown(
            "<div class='card-ghost'><div class='card-title'>Marketplace CRM cleanup</div>"
            "<div class='card-muted'>Unified 4 data sources into one pipeline with automatic routing and clean reporting.</div></div>",
            unsafe_allow_html=True,
        )
    with p3:
        st.markdown(
            "<div class='card-ghost'><div class='card-title'>Support triage automation</div>"
            "<div class='card-muted'>Cut ticket backlog by 38% with intent detection and instant follow-ups.</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<a id='demo'></a>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Try the demo</div>", unsafe_allow_html=True)
    st.info("Jump to the Chat page to run the live demo.")


if page == "Chat":
    st.markdown("<div class='section-title'>Lead Capture</div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Lead Capture</div>", unsafe_allow_html=True)

        with st.form("lead_capture"):
            lead_name = st.text_input("Name", "")
            lead_email = st.text_input("Work email", "")
            lead_company = st.text_input("Company", "")
            lead_crm = st.text_input("CRM used", "")
            lead_goal = st.text_area("What do you want to achieve?", "", height=100)
            lead_timeline = st.selectbox(
                "Timeline",
                ["This week", "This month", "This quarter", "Exploring"],
                index=1,
            )
            submit_lead = st.form_submit_button("Send to ClientOps")

        if submit_lead:
            lead_payload = {
                "name": lead_name.strip(),
                "email": lead_email.strip(),
                "company": lead_company.strip(),
                "crm": lead_crm.strip(),
                "goal": lead_goal.strip(),
                "timeline": lead_timeline,
            }
            message = compose_message_from_form(lead_payload)
            payload = {
                "message": message,
                "session_id": "demo-session",
            }
            if lead_payload["email"]:
                payload["email"] = lead_payload["email"]

            reply = safe_post_json(f"{API_URL}/chat", payload)
            if reply is not None:
                st.session_state["chat_reply"] = reply
                st.session_state["lead_payload"] = lead_payload

        st.divider()
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("View chat history", expanded=False):
            convo = safe_get_json(f"{API_URL}/conversations/demo-session")
            if convo and convo.get("messages"):
                for m in convo["messages"][-12:]:
                    role = m.get("role", "")
                    content = m.get("content", "")
                    if role == "user":
                        st.markdown(f"**User:** {content}")
                    elif role == "assistant":
                        st.markdown(f"**Assistant:** {content}")
                    else:
                        st.markdown(f"**System:** {content}")
            else:
                st.info("No messages yet. Send a message to start the transcript.")

    with col_right:
        reply = st.session_state.get("chat_reply")
        payload = st.session_state.get("lead_payload", {})
        topic = detect_topic((payload.get("goal") or "") + " " + (payload.get("crm") or "")) if payload else None
        intent = reply.get("triage", {}).get("intent") if reply else None
        routing = build_routing(intent)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Routing</div>", unsafe_allow_html=True)
        st.markdown(f"<span class='tag'>{routing}</span>", unsafe_allow_html=True)
        if intent:
            st.caption(f"Detected intent: {intent}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card' style='margin-top:12px;'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Assistant Reply</div>", unsafe_allow_html=True)
        if not reply:
            st.info("Send a message to see the assistant response.")
        else:
            st.write(reply.get("answer", ""))
            triage = reply.get("triage", {})
            if triage:
                st.caption(f"Intent: {triage.get('intent')} | Confidence: {triage.get('confidence')}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card' style='margin-top:12px;'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Recommended Service</div>", unsafe_allow_html=True)
        if topic:
            st.write(f"**{topic.get('name')}**")
            st.caption(topic.get("description"))
        else:
            st.info("Send a message so we can recommend the best service.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card' style='margin-top:12px;'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Follow-up Email Preview</div>", unsafe_allow_html=True)
        if reply:
            subject, body = build_followup_preview(intent, topic, payload)
            st.code(f"Subject: {subject}\n\n{body}", language="text")
        else:
            st.info("Send a message to generate a follow-up preview.")
        st.markdown("</div>", unsafe_allow_html=True)

    if "quick_chat" not in st.session_state:
        st.session_state["quick_chat"] = []

    with st.expander("Quick chat", expanded=False):
        qc_msg = st.text_input("Message", "", key="qc_msg")
        qc_email = st.text_input("Email", "", key="qc_email")
        if st.button("Send", key="qc_send"):
            payload = {"message": qc_msg, "session_id": "demo-session"}
            if qc_email.strip():
                payload["email"] = qc_email.strip()
            reply = safe_post_json(f"{API_URL}/chat", payload)
            if reply is not None:
                st.session_state["chat_reply"] = reply
                st.session_state["lead_payload"] = {"name": "", "email": qc_email.strip(), "goal": qc_msg}
                st.session_state["quick_chat"].append(
                    {"role": "user", "content": qc_msg}
                )
                st.session_state["quick_chat"].append(
                    {"role": "assistant", "content": reply.get("answer", "")}
                )

        history = st.session_state.get("quick_chat", [])[-6:]
        if history:
            st.divider()
            for m in history:
                role = m.get("role", "assistant")
                content = m.get("content", "")
                bubble_class = "chat-user" if role == "user" else "chat-assistant"
                st.markdown(
                    f'<div class="chat-bubble {bubble_class}">{content}</div>',
                    unsafe_allow_html=True,
                )


if page == "Admin":
    st.markdown("<div class='section-title'>Admin Workspace</div>", unsafe_allow_html=True)
    st.caption("Internal CRM view with lead updates, notes, and draft approvals.")

    admin_tabs = st.tabs(["Contacts", "Leads", "Tickets", "Conversation", "Drafts"])

    with admin_tabs[0]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if df_contacts.empty:
            st.info("No contacts yet.")
        else:
            preferred_cols = [c for c in ["id", "email", "name", "company"] if c in df_contacts.columns]
            other_cols = [c for c in df_contacts.columns if c not in preferred_cols]
            st.dataframe(df_contacts[preferred_cols + other_cols], use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with admin_tabs[1]:
        if df_leads.empty:
            st.info("No leads yet.")
        else:
            l1, l2 = st.columns(2)
            with l1:
                lead_status_options = ["(all)"]
                if "status" in df_leads.columns:
                    lead_status_options += sorted(df_leads["status"].dropna().unique().tolist())
                lead_status = st.selectbox("Lead status", lead_status_options, index=0)
            with l2:
                lead_contact = st.text_input("Filter by contact_id", value="")

            filtered = df_leads.copy()
            if "status" in filtered.columns and lead_status != "(all)":
                filtered = filtered[filtered["status"] == lead_status]

            if lead_contact.strip():
                try:
                    cid = int(lead_contact.strip())
                    if "contact_id" in filtered.columns:
                        filtered = filtered[filtered["contact_id"] == cid]
                except Exception:
                    st.warning("contact_id filter must be an integer.")

            preferred_cols = [c for c in ["id", "contact_id", "status", "score", "summary"] if c in filtered.columns]
            other_cols = [c for c in filtered.columns if c not in preferred_cols]

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.dataframe(filtered[preferred_cols + other_cols], use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-title'>Lead Actions</div>", unsafe_allow_html=True)
            u1, u2, u3, u4 = st.columns([2, 3, 2, 2])
            with u1:
                lead_id = st.number_input(
                    "Lead ID",
                    min_value=1,
                    value=int(df_leads["id"].max()) if "id" in df_leads.columns and len(df_leads) else 1,
                )
            with u2:
                new_status = st.selectbox(
                    "New status",
                    ["new", "open", "contacted", "qualified", "won", "lost", "duplicate"],
                    index=0,
                )
            with u3:
                new_score = st.number_input("Score (0-100)", min_value=0, max_value=100, value=50)
            with u4:
                do_update = st.button("Update lead")

            if do_update:
                payload = {"status": new_status, "score": int(new_score)}
                res = safe_patch_json(f"{API_URL}/admin/leads/{int(lead_id)}", payload)
                if res is not None:
                    st.success("Lead updated successfully.")
                    st.json(res)
                    st.rerun()

            st.divider()
            st.markdown("<div class='section-title'>Lead Notes + Timeline</div>", unsafe_allow_html=True)

            c1, c2 = st.columns([2, 3])
            with c1:
                timeline_lead_id = st.number_input(
                    "Timeline Lead ID",
                    min_value=1,
                    value=int(lead_id),
                    step=1,
                )
                if st.button("Load timeline"):
                    tl = safe_get_json(f"{API_URL}/admin/leads/{int(timeline_lead_id)}/timeline")
                    if tl is not None:
                        st.session_state["lead_timeline"] = tl

            with c2:
                note_text = st.text_area(
                    "Add note",
                    placeholder="Example: Spoke to customer, wants CRM + WhatsApp integration. Follow up Friday.",
                    height=120,
                )
                if st.button("Save note"):
                    if not note_text.strip():
                        st.warning("Please type a note first.")
                    else:
                        res = safe_post_json(
                            f"{API_URL}/admin/leads/{int(timeline_lead_id)}/notes",
                            {"note": note_text.strip(), "actor": "admin"},
                        )
                        if res is not None:
                            st.success("Note saved.")
                            tl = safe_get_json(f"{API_URL}/admin/leads/{int(timeline_lead_id)}/timeline")
                            if tl is not None:
                                st.session_state["lead_timeline"] = tl

            timeline = st.session_state.get("lead_timeline", [])
            if timeline:
                for e in timeline[::-1]:
                    etype = e.get("event_type")
                    actor = e.get("actor", "system")
                    ts = e.get("created_at", "")
                    st.write(f"**{etype}** | {actor} | {ts}")
                    if etype in ["status_changed", "score_changed"]:
                        st.code(f"{e.get('old_value')} -> {e.get('new_value')}", language="text")
                    else:
                        st.code(e.get("note") or "", language="text")
            else:
                st.info("No timeline loaded yet. Click **Load timeline**.")

    with admin_tabs[2]:
        if df_tickets.empty:
            st.info("No tickets yet.")
        else:
            t1, t2, t3 = st.columns(3)
            with t1:
                ticket_status_options = ["(all)"]
                if "status" in df_tickets.columns:
                    ticket_status_options += sorted(df_tickets["status"].dropna().unique().tolist())
                ticket_status = st.selectbox("Ticket status", ticket_status_options, index=0)
            with t2:
                ticket_priority_options = ["(all)"]
                if "priority" in df_tickets.columns:
                    ticket_priority_options += sorted(df_tickets["priority"].dropna().unique().tolist())
                ticket_priority = st.selectbox("Priority", ticket_priority_options, index=0)
            with t3:
                ticket_contact = st.text_input("Ticket contact_id", value="")

            filtered_t = df_tickets.copy()
            if "status" in filtered_t.columns and ticket_status != "(all)":
                filtered_t = filtered_t[filtered_t["status"] == ticket_status]
            if "priority" in filtered_t.columns and ticket_priority != "(all)":
                filtered_t = filtered_t[filtered_t["priority"] == ticket_priority]
            if ticket_contact.strip():
                try:
                    cid = int(ticket_contact.strip())
                    if "contact_id" in filtered_t.columns:
                        filtered_t = filtered_t[filtered_t["contact_id"] == cid]
                except Exception:
                    st.warning("contact_id filter must be an integer.")

            preferred_cols = [c for c in ["id", "contact_id", "status", "priority", "category", "summary"] if c in filtered_t.columns]
            other_cols = [c for c in filtered_t.columns if c not in preferred_cols]
            st.dataframe(filtered_t[preferred_cols + other_cols], use_container_width=True, hide_index=True)

    with admin_tabs[3]:
        session_id = st.text_input("Session ID", value="demo-session")
        convo = safe_get_json(f"{API_URL}/conversations/{session_id}")
        if convo is None:
            st.stop()

        st.write(f"**Session:** {convo.get('session_id')} | **Conversation ID:** {convo.get('conversation_id')}")
        messages = convo.get("messages", [])

        if not messages:
            st.info("No messages in this session yet.")
        else:
            last_n = st.slider("Show last N messages", min_value=5, max_value=100, value=25, step=5)
            show_msgs = messages[-last_n:]
            for m in show_msgs:
                role = m.get("role", "unknown")
                content = m.get("content", "")
                if role == "user":
                    st.markdown(f"User: {content}")
                elif role == "assistant":
                    st.markdown(f"Assistant: {content}")
                else:
                    st.markdown(f"System: {content}")

            drafts = [m for m in messages if m.get("role") == "system"]
            st.divider()
            st.markdown("Automation Drafts (System Messages)")
            if drafts:
                for d in drafts[-10:]:
                    st.code(d.get("content", ""), language="text")
            else:
                st.info("No automation drafts yet for this session.")

    with admin_tabs[4]:
        drafts = safe_get_json(f"{API_URL}/admin/drafts?status=pending")
        if drafts is None:
            st.stop()

        df_drafts = pd.DataFrame(drafts)
        if df_drafts.empty:
            st.info("No pending drafts.")
        else:
            st.dataframe(
                df_drafts[["id", "kind", "lead_id", "ticket_id", "contact_id", "created_at", "content"]],
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("#### Edit + Approve")

            dcol1, dcol2 = st.columns([2, 2])
            with dcol1:
                approve_id = st.number_input("Draft ID to approve", min_value=1, value=int(df_drafts["id"].iloc[0]))
            with dcol2:
                if st.button("Approve + Send"):
                    try:
                        r = httpx.post(f"{API_URL}/admin/drafts/{int(approve_id)}/approve", timeout=30)
                        r.raise_for_status()
                        st.success("Draft approved + sent (simulated). Lead auto-advanced.")
                        st.json(r.json())
                        st.rerun()
                    except Exception as e:
                        st.error(f"Approve failed: {e}")

            draft_row = df_drafts[df_drafts["id"] == int(approve_id)]
            if not draft_row.empty:
                draft_content = draft_row.iloc[0]["content"]
            else:
                draft_content = ""

            edited = st.text_area("Edit draft content", value=str(draft_content), height=160)
            c1, c2 = st.columns([2, 2])
            with c1:
                if st.button("Save Edit"):
                    res = safe_patch_json(
                        f"{API_URL}/admin/drafts/{int(approve_id)}",
                        {"content": edited},
                    )
                    if res is not None:
                        st.success("Draft updated.")
                        st.rerun()
            with c2:
                if st.button("Reject Draft"):
                    try:
                        r = httpx.post(f"{API_URL}/admin/drafts/{int(approve_id)}/reject", timeout=30)
                        r.raise_for_status()
                        st.success("Draft rejected.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Reject failed: {e}")
