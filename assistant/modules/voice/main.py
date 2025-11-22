"""
Voice & Chat UI (Streamlit) - API Version
==========================================
Clean Streamlit UI using unified Assistant API
With full conversational AI support
"""

import streamlit as st
from streamlit.runtime.scriptrunner import RerunException
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent.parent.parent  # asksharon_ai_blueprint
voice_dir = Path(__file__).parent  # voice module directory

for path in [project_root, voice_dir]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from assistant_api.app.client import AssistantAPIClient

# Import from refactored modules (direct imports since voice_dir is in sys.path)
from ui_styles import CUSTOM_CSS
from ui_components import check_api_health, render_item_card
from ui_forms import render_add_form
from conversation import process_chat_message
from actions import (
    execute_pending_action,
    get_daily_summary,
    check_and_summarize_emails,
    get_all_daily_tasks,
    # Email actions
    search_emails,
    fetch_new_emails,
    mark_email_read,
    mark_email_unread,
    star_email,
    detect_email_events,
    list_pending_events,
    approve_event,
    reject_event,
    # Calendar actions
    list_calendar_events,
    get_calendar_status,
    check_calendar_conflicts,
)

# Initialize API client
API_URL = "http://localhost:8002"
client = AssistantAPIClient(API_URL)

# Page config
st.set_page_config(
    page_title="AskSharon.ai",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def main():
    """Main Streamlit app - Chat-first design with full conversational AI"""

    # Show notifications
    if 'last_deleted' in st.session_state:
        st.toast(f"✅ Deleted: {st.session_state['last_deleted']}")
        del st.session_state['last_deleted']
    if 'last_updated' in st.session_state:
        st.toast(f"✅ Updated: {st.session_state['last_updated']}")
        del st.session_state['last_updated']

    # Check API health
    if not check_api_health(client):
        st.error(f"⚠️ Cannot connect to API at {API_URL}")
        st.info("Start API with: `uvicorn assistant_api.app.main:app --port 8002 --reload`")
        return

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "today"
    if 'awaiting_confirmation' not in st.session_state:
        st.session_state.awaiting_confirmation = False
    if 'pending_action' not in st.session_state:
        st.session_state.pending_action = None
    if 'pending_data' not in st.session_state:
        st.session_state.pending_data = None
    if 'awaiting_info' not in st.session_state:
        st.session_state.awaiting_info = False
    if 'awaiting_info_type' not in st.session_state:
        st.session_state.awaiting_info_type = None
    # Guided goal creation flow
    if 'goal_creation_stage' not in st.session_state:
        st.session_state.goal_creation_stage = None
    if 'pending_goal' not in st.session_state:
        st.session_state.pending_goal = {}

    # ===== HEADER =====
    st.title("🤖 AskSharon.ai")

    # ===== CHAT INPUT (Primary Interface) =====
    placeholder_text = _get_chat_placeholder()
    chat_input = st.chat_input(placeholder_text)

    if chat_input:
        _handle_chat_input(chat_input)

    # ===== DISPLAY RECENT CHAT =====
    if st.session_state.messages:
        for msg in st.session_state.messages[-6:]:  # Show last 6 messages
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    st.divider()

    # ===== QUICK ACTIONS =====
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📅 Today", use_container_width=True):
            st.session_state.current_view = "today"
    with col2:
        if st.button("🎯 Goals", use_container_width=True):
            st.session_state.current_view = "goals"
    with col3:
        if st.button("📆 Upcoming", use_container_width=True):
            st.session_state.current_view = "upcoming"
    with col4:
        if st.button("➕ Add New", use_container_width=True):
            st.session_state.current_view = "add_item"
            st.session_state.add_item_type = "task"

    st.divider()

    # ===== CONTENT AREA (based on current view) =====
    _render_content_area()

    # ===== SIDEBAR (Stats only) =====
    with st.sidebar:
        st.header("📊 Quick Stats")
        try:
            stats = client.get_stats()
            for item_type, count in stats['count_by_type'].items():
                type_name = item_type.replace("ItemType.", "")
                st.metric(type_name.title(), count)
        except Exception:
            pass


def _get_chat_placeholder() -> str:
    """Get appropriate placeholder text for chat input"""
    if st.session_state.awaiting_confirmation:
        return "Type 'yes' to confirm or 'no' to cancel..."
    elif st.session_state.goal_creation_stage:
        stage_hints = {
            'ask_calendar': "yes/no",
            'get_time': "e.g., 'weekdays 7:30-9am'",
            'get_name': "Enter goal name...",
            'get_category': "educational, fitness, work, personal, creative, other"
        }
        return stage_hints.get(st.session_state.goal_creation_stage, "Continue...")
    elif st.session_state.awaiting_info:
        return f"Enter the {st.session_state.awaiting_info_type.replace('_', ' ')}..."
    else:
        return "Ask Sharon anything... (e.g., 'create goal' or 'what's on today?')"


def _handle_chat_input(chat_input: str):
    """Process chat input and update state"""
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": chat_input})

    # Process message through conversational AI (pass history for LLM context)
    result = process_chat_message(chat_input, st.session_state.messages)

    # Handle confirmation responses
    if result['action'] == 'confirm_yes':
        # Execute the pending action
        if st.session_state.pending_action and st.session_state.pending_data:
            response = execute_pending_action(
                client,
                st.session_state.pending_data,
                st.session_state.pending_action
            )
        else:
            response = "Nothing to confirm."
        # Clear all confirmation and flow state
        st.session_state.awaiting_confirmation = False
        st.session_state.pending_action = None
        st.session_state.pending_data = None
        st.session_state.goal_creation_stage = None
        st.session_state.pending_goal = {}
        st.session_state.current_view = "today"

    elif result['action'] == 'confirm_no':
        response = "Okay, cancelled. What else can I help you with?"
        st.session_state.awaiting_confirmation = False
        st.session_state.pending_action = None
        st.session_state.pending_data = None
        st.session_state.goal_creation_stage = None
        st.session_state.pending_goal = {}

    elif result['action'] == 'show':
        st.session_state.current_view = result['view']
        response = result['response_text']
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'daily_summary':
        response = get_all_daily_tasks(client)
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'check_email':
        response = check_and_summarize_emails()
        st.session_state.awaiting_confirmation = False

    # EMAIL ACTIONS
    elif result['action'] == 'search_emails':
        response = search_emails(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'fetch_new_emails':
        response = fetch_new_emails(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'mark_email_read':
        response = mark_email_read(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'mark_email_unread':
        response = mark_email_unread(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'star_email':
        response = star_email(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'detect_email_events':
        response = detect_email_events(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'list_pending_events':
        response = list_pending_events(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'approve_event':
        response = approve_event(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'reject_event':
        response = reject_event(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    # CALENDAR ACTIONS
    elif result['action'] == 'list_calendar_events':
        response = list_calendar_events(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'calendar_status':
        response = get_calendar_status()
        st.session_state.awaiting_confirmation = False

    elif result['action'] == 'check_calendar_conflicts':
        response = check_calendar_conflicts(result['pending_data'])
        st.session_state.awaiting_confirmation = False

    elif result['action'] in ['goal_flow_start', 'goal_flow_continue']:
        response = result['response_text']

    elif result['action'] == 'need_goal_name':
        st.session_state.awaiting_info = True
        st.session_state.awaiting_info_type = 'goal_name'
        response = result['response_text']

    elif result['action'] == 'need_task_name':
        st.session_state.awaiting_info = True
        st.session_state.awaiting_info_type = 'task_name'
        response = result['response_text']

    elif result['action'] == 'need_more_info':
        info_needed = result.get('info_needed', '')
        if info_needed == 'calendar_preference':
            st.session_state.goal_creation_stage = 'ask_calendar'
            st.session_state.pending_goal = result.get('pending_data', {})
        elif info_needed == 'days':
            st.session_state.goal_creation_stage = 'get_time'
            st.session_state.pending_goal = result.get('pending_data', {})
        elif info_needed == 'time':
            st.session_state.goal_creation_stage = 'get_time'
            st.session_state.pending_goal = result.get('pending_data', {})
        response = result['response_text']

    elif result['needs_confirmation']:
        st.session_state.awaiting_confirmation = True
        st.session_state.pending_action = result['action']
        st.session_state.pending_data = result['pending_data']
        response = result['response_text']

    else:
        response = result['response_text']
        st.session_state.awaiting_confirmation = False
        st.session_state.awaiting_info = False

    st.session_state.messages.append({"role": "assistant", "content": response})


def _render_content_area():
    """Render the main content area based on current view"""
    current_view = st.session_state.current_view
    today = date.today()

    try:
        if current_view == "today":
            st.subheader("📅 Today's Schedule")
            result = client.list_items(date_from=today, date_to=today, limit=50)
            if result['total'] == 0:
                st.info("Nothing scheduled for today. Use the chat to add items!")
            else:
                for item in result['items']:
                    render_item_card(item, client, key_prefix="today")

        elif current_view == "goals":
            st.subheader("🎯 Your Goals")
            result = client.list_items(type=["goal"], limit=50)
            if result['total'] == 0:
                st.info("No goals yet. Try saying 'add a new goal'")
            else:
                for item in result['items']:
                    render_item_card(item, client, key_prefix="goals")

        elif current_view == "tasks":
            st.subheader("✅ Your Tasks")
            result = client.list_items(type=["task"], status="upcoming", limit=50)
            if result['total'] == 0:
                st.info("No pending tasks")
            else:
                for item in result['items']:
                    render_item_card(item, client, key_prefix="tasks")

        elif current_view == "upcoming":
            st.subheader("📆 Upcoming (Next 7 Days)")
            next_week = today + timedelta(days=7)
            result = client.list_items(date_from=today, date_to=next_week, limit=50)
            if result['total'] == 0:
                st.info("Nothing scheduled for the next 7 days")
            else:
                _render_upcoming_items(result['items'], today)

        elif current_view == "add_item":
            item_type = st.session_state.get('add_item_type', 'task')
            st.subheader(f"➕ Add New {item_type.title()}")
            render_add_form(item_type, client)

        elif current_view == "all":
            st.subheader("✅ All Items")
            result = client.list_items(limit=100)
            for item in result['items']:
                render_item_card(item, client, key_prefix="all")

    except RerunException:
        raise
    except Exception as e:
        st.error(f"Error: {e}")


def _render_upcoming_items(items, today):
    """Render items grouped by date"""
    items_by_date = {}
    for item in items:
        item_date = item['date']
        if item_date not in items_by_date:
            items_by_date[item_date] = []
        items_by_date[item_date].append(item)

    for item_date in sorted(items_by_date.keys()):
        date_obj = datetime.fromisoformat(item_date).date()
        days_away = (date_obj - today).days
        if days_away == 0:
            date_label = "Today"
        elif days_away == 1:
            date_label = "Tomorrow"
        else:
            date_label = date_obj.strftime("%A, %b %d")
        st.caption(f"**{date_label}**")
        for item in items_by_date[item_date]:
            render_item_card(item, client, key_prefix=f"upcoming_{item_date}")


if __name__ == "__main__":
    main()
