import os
import streamlit as st
import httpx
import pandas as pd

# Use env var in docker; defaults to docker service name
API_URL = os.getenv("API_URL", "http://api:8000")
# If running UI locally (outside docker), set:
#API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="ClientOps AI", layout="wide")
st.title("ClientOps AI (Demo)")

tab1, tab2 = st.tabs(["Chat", "Admin Dashboard"])

with tab1:
    st.subheader("Chat (placeholder)")
    email = st.text_input("Email (optional)", "")
    msg = st.text_input("Message", "What services do you offer?")

    if st.button("Send"):
        try:
            payload = {"message": msg, "session_id": "demo-session"}
            if email.strip():
                payload["email"] = email.strip()

            r = httpx.post(f"{API_URL}/chat", json=payload, timeout=30)
            st.json(r.json())
        except Exception as e:
            st.error(f"API error: {e}")

with tab2:
    st.subheader("Admin Dashboard")
    st.caption("Internal CRM view (contacts, leads, tickets) + automation drafts.")

    # ---- helpers ----
    def safe_get_json(url: str):
        try:
            r = httpx.get(url, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            st.error(f"API error calling {url}: {e}")
            return None

    # ---- controls ----
    colA, colB, colC = st.columns([2, 2, 3])
    with colA:
        session_id = st.text_input("Session ID", value="demo-session")
    with colB:
        _ = st.button("Refresh tables")  # Streamlit reruns anyway
    with colC:
        st.info("Tip: Use filters below to view only 'new' leads or 'open' tickets.")

    st.divider()

    # ---- load data ----
    contacts = safe_get_json(f"{API_URL}/admin/contacts")
    leads = safe_get_json(f"{API_URL}/admin/leads")
    tickets = safe_get_json(f"{API_URL}/admin/tickets")
    convo = safe_get_json(f"{API_URL}/conversations/{session_id}")

    # ---- tables: Contacts ----
    st.markdown("### Contacts")
    if contacts is None:
        st.stop()

    df_contacts = pd.DataFrame(contacts)
    if df_contacts.empty:
        st.warning("No contacts yet.")
    else:
        preferred_cols = [c for c in ["id", "email", "name", "company"] if c in df_contacts.columns]
        other_cols = [c for c in df_contacts.columns if c not in preferred_cols]
        df_contacts = df_contacts[preferred_cols + other_cols]
        st.dataframe(df_contacts, use_container_width=True, hide_index=True)

    st.divider()

    # ---- tables: Leads + filters ----
    st.markdown("### Leads")
    if leads is None:
        st.stop()

    df_leads = pd.DataFrame(leads)
    st.caption(f"Rows: {len(df_leads)}")

    if df_leads.empty:
        st.warning("No leads yet.")
    else:
        f1, f2 = st.columns(2)
        with f1:
            lead_status_options = ["(all)"]
            if "status" in df_leads.columns:
                lead_status_options += sorted(df_leads["status"].dropna().unique().tolist())
            lead_status = st.selectbox("Lead status", lead_status_options, index=0)

        with f2:
            lead_contact = st.text_input("Filter by contact_id (optional)", value="")

        filtered = df_leads.copy()

        if "status" in filtered.columns and lead_status != "(all)":
            filtered = filtered[filtered["status"] == lead_status]

        if lead_contact.strip():
            try:
                cid = int(lead_contact.strip())
                if "contact_id" in filtered.columns:
                    filtered = filtered[filtered["contact_id"] == cid]
            except:
                st.warning("contact_id filter must be an integer.")

        preferred_cols = [c for c in ["id", "contact_id", "status", "score", "summary"] if c in filtered.columns]
        other_cols = [c for c in filtered.columns if c not in preferred_cols]
        filtered = filtered[preferred_cols + other_cols]

        st.dataframe(filtered, use_container_width=True, hide_index=True)

        # ---- Lead Update UI (Status / Score) ----
        st.divider()
        st.markdown("### Update Lead (Status / Score)")

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
            try:
                payload = {"status": new_status, "score": int(new_score)}
                r = httpx.patch(
                    f"{API_URL}/admin/leads/{int(lead_id)}",
                    json=payload,
                    timeout=30,
                )
                r.raise_for_status()
                st.success("Lead updated successfully..!")
                st.json(r.json())

                # Refresh the page / tables
                st.rerun()

            except Exception as e:
                st.error(f"Update failed: {e}")

                # ---- Lead Notes + Timeline ----
        st.divider()
        st.markdown("### Lead Notes + Timeline")

        # Keep timeline lead_id in sync with the update lead_id
        timeline_lead_id = int(lead_id)

        c1, c2 = st.columns([2, 3])

        with c1:
            timeline_lead_id = st.number_input(
                "Timeline Lead ID",
                min_value=1,
                value=timeline_lead_id,
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
                    try:
                        r = httpx.post(
                            f"{API_URL}/admin/leads/{int(timeline_lead_id)}/notes",
                            json={"note": note_text.strip(), "actor": "admin"},
                            timeout=30,
                        )
                        r.raise_for_status()
                        st.success("Note saved ✅")

                        # Refresh timeline after save
                        tl = safe_get_json(f"{API_URL}/admin/leads/{int(timeline_lead_id)}/timeline")
                        if tl is not None:
                            st.session_state["lead_timeline"] = tl

                    except Exception as e:
                        st.error(f"Note save failed: {e}")

        # Render timeline (newest first)
        timeline = st.session_state.get("lead_timeline", [])

        if timeline:
            st.markdown("#### Timeline (Newest first)")
            for e in timeline[::-1]:
                etype = e.get("event_type")
                actor = e.get("actor", "system")
                ts = e.get("created_at", "")

                st.write(f"**{etype}** • {actor} • {ts}")

                if etype in ["status_changed", "score_changed"]:
                    st.code(f"{e.get('old_value')} -> {e.get('new_value')}", language="text")
                else:
                    st.code(e.get("note") or "", language="text")
        else:
            st.info("No timeline loaded yet. Click **Load timeline**.")

    st.divider()

    # ---- tables: Tickets + filters ----
    st.markdown("### Tickets")
    if tickets is None:
        st.stop()

    df_tickets = pd.DataFrame(tickets)
    if df_tickets.empty:
        st.warning("No tickets yet.")
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
            ticket_contact = st.text_input("Ticket contact_id (optional)", value="")

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
            except:
                st.warning("contact_id filter must be an integer.")

        preferred_cols = [c for c in ["id", "contact_id", "status", "priority", "category", "summary"] if c in filtered_t.columns]
        other_cols = [c for c in filtered_t.columns if c not in preferred_cols]
        filtered_t = filtered_t[preferred_cols + other_cols]

        st.dataframe(filtered_t, use_container_width=True, hide_index=True)

    st.divider()

    # ---- conversation viewer + automation drafts ----
    st.markdown(" Conversation Viewer")
    if convo is None:
        st.stop()

    st.write(f"**Session:** {convo.get('session_id')}  |  **Conversation ID:** {convo.get('conversation_id')}")
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
                st.markdown(f" System: {content}")

        drafts = [m for m in messages if m.get("role") == "system"]
        st.divider()
        st.markdown("Automation Drafts (System Messages)")
        if drafts:
            for d in drafts[-10:]:
                st.code(d.get("content", ""), language="text")
        else:
            st.info("No automation drafts yet for this session.")
    

    st.divider()
    st.markdown("### Approve Drafts")

    drafts = safe_get_json(f"{API_URL}/admin/drafts?status=pending")
    if drafts is None:
        st.stop()

    df_drafts = pd.DataFrame(drafts)
    if df_drafts.empty:
        st.info("No pending drafts.")
    else:
        st.dataframe(df_drafts[["id","kind","lead_id","ticket_id","contact_id","created_at","content"]], use_container_width=True, hide_index=True)

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