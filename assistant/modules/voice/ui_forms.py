"""
UI Forms
========
Form components for the Streamlit UI.
"""

import streamlit as st
from streamlit.runtime.scriptrunner import RerunException
from datetime import date


def render_add_form(item_type: str, client):
    """Render form for adding new items."""
    with st.form("add_item_form", clear_on_submit=True):
        title = st.text_input("Title", placeholder=f"Enter {item_type} title...")
        description = st.text_area("Description (optional)", placeholder="Add details...")

        col1, col2 = st.columns(2)
        with col1:
            item_date = st.date_input("Date", value=date.today())
        with col2:
            priority = st.selectbox("Priority", [None, "low", "med", "high"])

        # For sessions, allow linking to a goal and add time
        goal_id = None
        start_time = None
        end_time = None
        if item_type == "session":
            st.caption("Link this session to a goal")
            # Get existing goals
            try:
                goals_result = client.list_items(type=["goal"], limit=50)
                goal_options = {g['title']: g['id'] for g in goals_result['items']}
                if goal_options:
                    selected_goal = st.selectbox("Goal", options=["None"] + list(goal_options.keys()))
                    if selected_goal != "None":
                        goal_id = goal_options[selected_goal]
                else:
                    st.info("No goals yet. Create a goal first to link sessions.")
            except Exception:
                pass

            col3, col4 = st.columns(2)
            with col3:
                start_time = st.time_input("Start Time")
            with col4:
                end_time = st.time_input("End Time")

        if st.form_submit_button(f"Create {item_type.title()}", use_container_width=True):
            if title:
                try:
                    new_item = {
                        "type": item_type,
                        "title": title,
                        "description": description if description else None,
                        "date": str(item_date),
                        "status": "upcoming",
                        "source": "manual",
                    }
                    if priority:
                        new_item["priority"] = priority
                    if goal_id:
                        new_item["goal_id"] = goal_id
                    if start_time:
                        new_item["start_time"] = start_time.strftime("%H:%M")
                    if end_time:
                        new_item["end_time"] = end_time.strftime("%H:%M")

                    client.create_item(new_item)
                    st.success(f"Created: {title}")
                    st.session_state.current_view = "today"
                    st.rerun()
                except RerunException:
                    raise
                except Exception as e:
                    st.error(f"Error creating item: {e}")
            else:
                st.warning("Please enter a title")
