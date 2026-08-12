"""
Support Ticket App — Databricks App backed by Lakebase (Postgres).

Uses lakebase.py for all reads/writes, which authenticates via a single
LAKEBASE_URL secret (native Postgres password) instead of OAuth tokens.
"""

import streamlit as st
import lakebase

st.set_page_config(page_title="Support Ticket System", page_icon="🎫", layout="wide")

SCHEMA = "support"
STATUS_OPTIONS = ["open", "in_progress", "resolved", "closed"]
PRIORITY_OPTIONS = ["low", "medium", "high", "urgent"]
CATEGORY_OPTIONS = ["general", "bug", "access", "feature_request", "billing"]
STATUS_EMOJI = {"open": "🔴", "in_progress": "🟡", "resolved": "🟢", "closed": "⚪"}

st.title("🎫 Support Ticket System")
st.caption("Backed by Lakebase — all reads and writes hit Postgres directly.")


def safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        return None, str(e)


# ------------------------------------------------------------------
# Data access functions (thin wrappers around lakebase.py)
# ------------------------------------------------------------------
def list_tickets(status_filter=None):
    sql = f"""
        SELECT t.ticket_id, t.title, t.status, t.priority, t.category,
               t.created_by, t.created_at, t.updated_at,
               COUNT(m.message_id) AS message_count
        FROM {SCHEMA}.tickets t
        LEFT JOIN {SCHEMA}.ticket_messages m ON m.ticket_id = t.ticket_id
        {{where}}
        GROUP BY t.ticket_id
        ORDER BY t.created_at DESC
    """
    where, params = "", None
    if status_filter and status_filter != "All":
        where, params = "WHERE t.status = %s", (status_filter,)
    return lakebase.run_query(sql.format(where=where), params)


def get_ticket(ticket_id):
    rows = lakebase.run_query(
        f"SELECT * FROM {SCHEMA}.tickets WHERE ticket_id = %s", (ticket_id,)
    )
    return rows[0] if rows else None


def create_ticket(title, priority, category, created_by):
    row = lakebase.run_write_returning(
        f"""
        INSERT INTO {SCHEMA}.tickets (title, priority, category, created_by)
        VALUES (%s, %s, %s, %s)
        RETURNING ticket_id
        """,
        (title, priority, category, created_by),
    )
    return row["ticket_id"]


def update_ticket_status(ticket_id, status):
    lakebase.run_write(
        f"UPDATE {SCHEMA}.tickets SET status = %s, updated_at = now() WHERE ticket_id = %s",
        (status, ticket_id),
    )


def delete_ticket(ticket_id):
    lakebase.run_write(f"DELETE FROM {SCHEMA}.tickets WHERE ticket_id = %s", (ticket_id,))


def list_messages(ticket_id):
    return lakebase.run_query(
        f"SELECT * FROM {SCHEMA}.ticket_messages WHERE ticket_id = %s ORDER BY created_at ASC",
        (ticket_id,),
    )


def add_message(ticket_id, message, author):
    row = lakebase.run_write_returning(
        f"""
        INSERT INTO {SCHEMA}.ticket_messages (ticket_id, message, author)
        VALUES (%s, %s, %s)
        RETURNING message_id
        """,
        (ticket_id, message, author),
    )
    return row["message_id"]


def ticket_stats():
    return lakebase.run_query(
        f"SELECT status, COUNT(*) AS count FROM {SCHEMA}.tickets GROUP BY status"
    )


# ------------------------------------------------------------------
# Sidebar: stats + create ticket
# ------------------------------------------------------------------
with st.sidebar:
    st.header("📊 Ticket Stats")
    stats, err = safe_call(ticket_stats)
    if err:
        st.error(f"Could not load stats: {err}")
    elif stats:
        for row in stats:
            st.metric(row["status"].replace("_", " ").title(), row["count"])
    else:
        st.info("No tickets yet.")

    st.divider()
    st.header("➕ New Ticket")
    with st.form("create_ticket_form", clear_on_submit=True):
        new_title = st.text_input("Title *", max_chars=255)
        new_priority = st.selectbox("Priority", PRIORITY_OPTIONS, index=1)
        new_category = st.selectbox("Category", CATEGORY_OPTIONS)
        new_author = st.text_input(
            "Your name *", value=st.session_state.get("username", ""), max_chars=64
        )
        submitted = st.form_submit_button("Create Ticket", use_container_width=True)

        if submitted:
            if not new_title.strip():
                st.error("Title is required.")
            elif not new_author.strip():
                st.error("Your name is required.")
            else:
                st.session_state["username"] = new_author.strip()
                _, err = safe_call(
                    create_ticket, new_title.strip(), new_priority, new_category, new_author.strip()
                )
                if err:
                    st.error(f"Failed to create ticket: {err}")
                else:
                    st.success("Ticket created!")
                    st.rerun()

# ------------------------------------------------------------------
# Main: ticket list with status filter
# ------------------------------------------------------------------
col_filter, _ = st.columns([1, 3])
with col_filter:
    status_filter = st.selectbox("Filter by status", ["All"] + STATUS_OPTIONS)

tickets, err = safe_call(list_tickets, status_filter)
if err:
    st.error(f"Could not load tickets from Lakebase: {err}")
    st.stop()

if not tickets:
    st.info("No tickets match this filter yet. Create one from the sidebar.")
    st.stop()

st.subheader(f"All Tickets ({len(tickets)})")

for t in tickets:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([4, 1.2, 1.2, 1])
        with c1:
            st.markdown(f"**#{t['ticket_id']} — {t['title']}**")
            st.caption(
                f"by {t['created_by']} · {t['created_at']:%Y-%m-%d %H:%M} · {t['message_count']} message(s)"
            )
        with c2:
            st.write(f"{STATUS_EMOJI.get(t['status'], '')} {t['status'].replace('_',' ').title()}")
        with c3:
            st.write(f"Priority: {t['priority'].title()}")
        with c4:
            if st.button("Open", key=f"open_{t['ticket_id']}"):
                st.session_state["selected_ticket"] = t["ticket_id"]
                st.rerun()

# ------------------------------------------------------------------
# Detail view
# ------------------------------------------------------------------
selected_id = st.session_state.get("selected_ticket")
if selected_id:
    st.divider()
    ticket, err = safe_call(get_ticket, selected_id)
    if err or not ticket:
        st.error("Could not load that ticket. It may have been deleted.")
        st.session_state["selected_ticket"] = None
    else:
        st.header(f"#{ticket['ticket_id']} — {ticket['title']}")

        cA, cC = st.columns([2, 1])
        with cA:
            new_status = st.selectbox(
                "Update status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(ticket["status"]) if ticket["status"] in STATUS_OPTIONS else 0,
                key=f"status_select_{ticket['ticket_id']}",
            )
            if st.button("Save status", key=f"save_status_{ticket['ticket_id']}"):
                _, err = safe_call(update_ticket_status, ticket["ticket_id"], new_status)
                if err:
                    st.error(f"Failed to update status: {err}")
                else:
                    st.success("Status updated.")
                    st.rerun()
        with cC:
            st.write("")
            confirm_key = f"confirm_delete_{ticket['ticket_id']}"
            if st.session_state.get(confirm_key):
                st.warning("Delete this ticket and all its messages?")
                dc1, dc2 = st.columns(2)
                if dc1.button("Yes, delete", key=f"del_yes_{ticket['ticket_id']}"):
                    _, err = safe_call(delete_ticket, ticket["ticket_id"])
                    if err:
                        st.error(f"Failed to delete: {err}")
                    else:
                        st.session_state["selected_ticket"] = None
                        st.session_state[confirm_key] = False
                        st.success("Ticket deleted.")
                        st.rerun()
                if dc2.button("Cancel", key=f"del_no_{ticket['ticket_id']}"):
                    st.session_state[confirm_key] = False
                    st.rerun()
            else:
                if st.button("🗑 Delete ticket", key=f"del_btn_{ticket['ticket_id']}"):
                    st.session_state[confirm_key] = True
                    st.rerun()

        st.subheader("Messages")
        messages, err = safe_call(list_messages, ticket["ticket_id"])
        if err:
            st.error(f"Could not load messages: {err}")
        else:
            if not messages:
                st.caption("No messages yet.")
            for m in messages:
                st.markdown(f"**{m['author']}** · _{m['created_at']:%Y-%m-%d %H:%M}_")
                st.write(m["message"])
                st.markdown("---")

        with st.form(f"add_message_form_{ticket['ticket_id']}", clear_on_submit=True):
            msg_author = st.text_input("Your name", value=st.session_state.get("username", ""), max_chars=64)
            msg_text = st.text_area("Add a message", max_chars=1000)
            msg_submit = st.form_submit_button("Add message")
            if msg_submit:
                if not msg_text.strip():
                    st.error("Message text cannot be empty.")
                elif not msg_author.strip():
                    st.error("Your name is required.")
                else:
                    st.session_state["username"] = msg_author.strip()
                    _, err = safe_call(add_message, ticket["ticket_id"], msg_text.strip(), msg_author.strip())
                    if err:
                        st.error(f"Failed to add message: {err}")
                    else:
                        st.success("Message added.")
                        st.rerun()

        if st.button("← Back to all tickets"):
            st.session_state["selected_ticket"] = None
            st.rerun()
