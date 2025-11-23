"""
UI Components
=============
Reusable Streamlit UI components.
"""

import streamlit as st
from streamlit.runtime.scriptrunner import RerunException
from datetime import datetime
import urllib.parse


def check_api_health(client) -> bool:
    """Check if API is available"""
    try:
        health = client.health_check()
        return health["status"] == "ok"
    except Exception:
        return False


def add_to_google_calendar(item):
    """Generate Google Calendar link for an item."""
    title = item.get("title", "Event")
    date_str = item.get("date", "")
    start_time = item.get("start_time") or "09:00"
    end_time = item.get("end_time") or "10:00"
    location = item.get("location") or ""
    description = item.get("description") or ""

    # Format dates for Google Calendar (YYYYMMDDTHHMMSS)
    if date_str and start_time:
        date_clean = date_str.replace("-", "")
        start_clean = start_time.replace(":", "") if ":" in start_time else start_time + "00"
        end_clean = end_time.replace(":", "") if ":" in end_time else end_time + "00"
        start_dt = f"{date_clean}T{start_clean}00"
        end_dt = f"{date_clean}T{end_clean}00"
    else:
        return None

    # URL encode parameters
    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start_dt}/{end_dt}",
        "details": description,
        "location": location,
    }
    base_url = "https://calendar.google.com/calendar/render"
    return f"{base_url}?{urllib.parse.urlencode(params)}"


TYPE_EMOJI = {
    "appointment": "📅",
    "meeting": "👥",
    "task": "✅",
    "goal": "🎯",
    "webinar": "📺",
    "session": "⏰",
}


def render_item_card(item, client, key_prefix=""):
    """Render a single item card"""
    is_webinar = item.get("type") == "webinar"

    with st.container():
        # Extra column for webinars (calendar button)
        if is_webinar:
            col1, col2, col3, col4, col5 = st.columns([3, 1, 0.7, 0.7, 0.7])
        else:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            # Title (clickable if has URL)
            title = item["title"]
            if item.get("gmail_thread_url"):
                st.markdown(
                    f"**{TYPE_EMOJI.get(item['type'], '📄')} [{title}]({item['gmail_thread_url']})**"
                )
            elif item.get("calendar_event_url"):
                st.markdown(
                    f"**{TYPE_EMOJI.get(item['type'], '📄')} [{title}]({item['calendar_event_url']})**"
                )
            else:
                st.markdown(f"**{TYPE_EMOJI.get(item['type'], '📄')} {title}**")

            # Meta info
            meta_parts = []
            if item.get("start_time"):
                meta_parts.append(f"🕐 {item['start_time']}")
            if item.get("location"):
                meta_parts.append(f"📍 {item['location']}")
            if item.get("participants"):
                meta_parts.append(f"👤 {len(item['participants'])} participants")

            if meta_parts:
                st.caption(" • ".join(meta_parts))

            if item.get("description"):
                st.caption(item["description"])

        with col2:
            # Type and status badges
            st.markdown(
                f'<span class="badge badge-{item["type"]}">{item["type"]}</span>'
                f'<span class="badge badge-{item["status"]}">{item["status"]}</span>',
                unsafe_allow_html=True,
            )
            if item.get("priority"):
                st.markdown(
                    f'<span class="badge badge-{item["priority"]}">{item["priority"]}</span>',
                    unsafe_allow_html=True,
                )

        with col3:
            # Edit button
            if st.button("✏️ Edit", key=f"{key_prefix}_edit_{item['id']}"):
                st.session_state[f"editing_{item['id']}"] = True
                st.rerun()

        with col4:
            # Delete button - use session state to trigger rerun cleanly
            if st.button("🗑️ Delete", key=f"{key_prefix}_delete_{item['id']}"):
                try:
                    client.delete_item(item["id"])
                    st.session_state["last_deleted"] = item["title"]
                    st.rerun()
                except RerunException:
                    raise  # Let Streamlit handle the rerun
                except Exception as e:
                    st.error(f"Error deleting: {e}")

        # Add to Calendar button for webinars
        if is_webinar:
            with col5:
                cal_url = add_to_google_calendar(item)
                if cal_url:
                    st.link_button("📅", cal_url, help="Add to Google Calendar")

        # Edit form (shown if editing)
        if st.session_state.get(f"editing_{item['id']}", False):
            _render_edit_form(item, client, key_prefix)

        st.divider()


def _render_edit_form(item, client, key_prefix):
    """Render edit form for an item"""
    with st.form(key=f"{key_prefix}_form_{item['id']}"):
        st.subheader("Edit Item")

        col1, col2 = st.columns(2)
        with col1:
            new_title = st.text_input("Title", value=item["title"])
            new_status = st.selectbox(
                "Status",
                ["upcoming", "in_progress", "done", "overdue"],
                index=["upcoming", "in_progress", "done", "overdue"].index(item["status"]),
            )

        with col2:
            new_date = st.date_input("Date", value=datetime.fromisoformat(str(item["date"])))
            new_priority = st.selectbox(
                "Priority",
                [None, "low", "med", "high"],
                index=[None, "low", "med", "high"].index(item.get("priority")),
            )

        new_description = st.text_area("Description", value=item.get("description") or "")

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save"):
                updates = {
                    "title": new_title,
                    "status": new_status,
                    "date": str(new_date),
                    "description": new_description if new_description else None,
                }
                # Only include priority if set (avoid sending None as string)
                if new_priority:
                    updates["priority"] = new_priority
                try:
                    client.update_item(item["id"], updates)
                    st.session_state[f"editing_{item['id']}"] = False
                    st.session_state["last_updated"] = item["title"]
                    st.rerun()
                except RerunException:
                    raise
                except Exception as e:
                    st.error(f"Error saving: {e}")

        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state[f"editing_{item['id']}"] = False
                st.rerun()
