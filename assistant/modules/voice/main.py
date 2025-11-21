"""
Voice & Chat UI (Streamlit) - API Version
==========================================
Clean Streamlit UI using unified Assistant API
"""

import streamlit as st
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent.parent
assistant_root = Path(__file__).parent.parent.parent / "assistant"

for path in [project_root, assistant_root]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.api_client import AssistantAPIClient

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
st.markdown("""
<style>
    .item-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
        background: white;
    }
    .item-title {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.25rem;
    }
    .item-meta {
        color: #666;
        font-size: 0.9rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 0.5rem;
    }
    .badge-appointment { background: #e3f2fd; color: #1976d2; }
    .badge-meeting { background: #f3e5f5; color: #7b1fa2; }
    .badge-task { background: #fff3e0; color: #f57c00; }
    .badge-goal { background: #e8f5e9; color: #388e3c; }
    .badge-upcoming { background: #e0f2f1; color: #00897b; }
    .badge-in_progress { background: #fff9c4; color: #f57f17; }
    .badge-done { background: #c8e6c9; color: #2e7d32; }
    .badge-high { background: #ffebee; color: #c62828; }
    .badge-med { background: #fff3e0; color: #ef6c00; }
    .badge-low { background: #f1f8e9; color: #689f38; }
</style>
""", unsafe_allow_html=True)


def check_api_health():
    """Check if API is available"""
    try:
        health = client.health_check()
        return health['status'] == 'ok'
    except:
        return False


def render_item_card(item, key_prefix=""):
    """Render a single item card"""
    type_emoji = {
        "appointment": "📅",
        "meeting": "👥",
        "task": "✅",
        "goal": "🎯"
    }

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            # Title (clickable if has URL)
            title = item['title']
            if item.get('gmail_thread_url'):
                st.markdown(f"**{type_emoji.get(item['type'], '📄')} [{title}]({item['gmail_thread_url']})**")
            elif item.get('calendar_event_url'):
                st.markdown(f"**{type_emoji.get(item['type'], '📄')} [{title}]({item['calendar_event_url']})**")
            else:
                st.markdown(f"**{type_emoji.get(item['type'], '📄')} {title}**")

            # Meta info
            meta_parts = []
            if item.get('start_time'):
                meta_parts.append(f"🕐 {item['start_time']}")
            if item.get('location'):
                meta_parts.append(f"📍 {item['location']}")
            if item.get('participants'):
                meta_parts.append(f"👤 {len(item['participants'])} participants")

            if meta_parts:
                st.caption(" • ".join(meta_parts))

            if item.get('description'):
                st.caption(item['description'])

        with col2:
            # Type and status badges
            st.markdown(
                f'<span class="badge badge-{item["type"]}">{item["type"]}</span>'
                f'<span class="badge badge-{item["status"]}">{item["status"]}</span>',
                unsafe_allow_html=True
            )
            if item.get('priority'):
                st.markdown(
                    f'<span class="badge badge-{item["priority"]}">{item["priority"]}</span>',
                    unsafe_allow_html=True
                )

        with col3:
            # Edit button
            if st.button("✏️ Edit", key=f"{key_prefix}_edit_{item['id']}"):
                st.session_state[f"editing_{item['id']}"] = True
                st.rerun()

        with col4:
            # Delete button
            if st.button("🗑️ Delete", key=f"{key_prefix}_delete_{item['id']}"):
                try:
                    client.delete_item(item['id'])
                    st.success(f"Deleted: {item['title']}")
                    st.rerun()
                except Exception as e:
                    if "RerunData" not in str(type(e)):
                        st.error(f"Error deleting: {e}")

        # Edit form (shown if editing)
        if st.session_state.get(f"editing_{item['id']}", False):
            with st.form(key=f"{key_prefix}_form_{item['id']}"):
                st.subheader("Edit Item")

                col1, col2 = st.columns(2)
                with col1:
                    new_title = st.text_input("Title", value=item['title'])
                    new_status = st.selectbox(
                        "Status",
                        ["upcoming", "in_progress", "done", "overdue"],
                        index=["upcoming", "in_progress", "done", "overdue"].index(item['status'])
                    )

                with col2:
                    new_date = st.date_input("Date", value=datetime.fromisoformat(str(item['date'])))
                    new_priority = st.selectbox(
                        "Priority",
                        [None, "low", "med", "high"],
                        index=[None, "low", "med", "high"].index(item.get('priority'))
                    )

                new_description = st.text_area("Description", value=item.get('description') or "")

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save"):
                        updates = {
                            "title": new_title,
                            "status": new_status,
                            "date": str(new_date),
                            "description": new_description if new_description else None,
                            "priority": new_priority
                        }
                        client.update_item(item['id'], updates)
                        st.session_state[f"editing_{item['id']}"] = False
                        st.success("Updated!")
                        st.rerun()

                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state[f"editing_{item['id']}"] = False
                        st.rerun()

        st.divider()


def main():
    """Main Streamlit app"""

    # Header
    st.title("🤖 AskSharon.ai")

    # Check API health
    if not check_api_health():
        st.error(f"⚠️ Cannot connect to API at {API_URL}")
        st.info("Start API with: `uvicorn assistant_api.app.main:app --port 8002 --reload`")
        return

    # Sidebar
    with st.sidebar:
        st.header("📊 Dashboard")

        # Get stats
        try:
            stats = client.get_stats()

            st.subheader("By Type")
            for item_type, count in stats['count_by_type'].items():
                type_name = item_type.replace("ItemType.", "")
                st.metric(type_name.title(), count)

            st.divider()

            st.subheader("Today")
            st.metric("Total Today", stats['today']['total'])
            for item_type, count in stats['today'].get('by_type', {}).items():
                type_name = item_type.replace("ItemType.", "")
                st.caption(f"{type_name}: {count}")

        except Exception as e:
            st.error(f"Error loading stats: {e}")

        st.divider()

        # Filters
        st.header("🔍 Filters")
        filter_type = st.multiselect(
            "Type",
            ["appointment", "meeting", "task", "goal"],
            default=None
        )

        filter_status = st.selectbox(
            "Status",
            [None, "upcoming", "in_progress", "done", "overdue"]
        )

        filter_source = st.selectbox(
            "Source",
            [None, "manual", "gmail", "calendar"]
        )

        st.divider()

        # Add new item
        if st.button("➕ Add New Item"):
            st.session_state['show_add_form'] = True

    # Main content area
    tabs = st.tabs(["📅 Today", "📆 Upcoming", "✅ All Items", "➕ Add New"])

    # Tab 1: Today
    with tabs[0]:
        st.header("Today's Items")
        today = date.today()

        try:
            result = client.list_items(
                date_from=today,
                date_to=today,
                status="upcoming" if not filter_status else filter_status,
                type=filter_type if filter_type else None,
                limit=100
            )

            if result['total'] == 0:
                st.info("No items for today")
            else:
                st.caption(f"Showing {len(result['items'])} of {result['total']} items")
                for item in result['items']:
                    render_item_card(item, key_prefix="today")

        except Exception as e:
            # Ignore RerunData exceptions (these are expected from st.rerun())
            if "RerunData" not in str(type(e).__name__):
                st.error(f"Error loading items: {e}")

    # Tab 2: Upcoming (next 7 days)
    with tabs[1]:
        st.header("Upcoming (Next 7 Days)")
        today = date.today()
        next_week = today + timedelta(days=7)

        try:
            result = client.list_items(
                date_from=today,
                date_to=next_week,
                status=filter_status,
                type=filter_type if filter_type else None,
                source=filter_source,
                limit=100
            )

            if result['total'] == 0:
                st.info("No upcoming items")
            else:
                st.caption(f"Showing {len(result['items'])} of {result['total']} items")

                # Group by date
                items_by_date = {}
                for item in result['items']:
                    item_date = item['date']
                    if item_date not in items_by_date:
                        items_by_date[item_date] = []
                    items_by_date[item_date].append(item)

                # Display grouped by date
                for item_date in sorted(items_by_date.keys()):
                    date_obj = datetime.fromisoformat(item_date).date()
                    days_away = (date_obj - today).days

                    if days_away == 0:
                        date_label = "Today"
                    elif days_away == 1:
                        date_label = "Tomorrow"
                    else:
                        date_label = date_obj.strftime("%A, %b %d")

                    st.subheader(f"{date_label} ({len(items_by_date[item_date])} items)")

                    for item in items_by_date[item_date]:
                        render_item_card(item, key_prefix=f"upcoming_{item_date}")

        except Exception as e:
            # Ignore RerunData exceptions (these are expected from st.rerun())
            if "RerunData" not in str(type(e).__name__):
                st.error(f"Error loading items: {e}")

    # Tab 3: All Items
    with tabs[2]:
        st.header("All Items")

        # Search
        search_query = st.text_input("🔍 Search", placeholder="Search title, description, location...")

        # Pagination
        col1, col2 = st.columns([1, 3])
        with col1:
            limit = st.selectbox("Items per page", [10, 25, 50, 100], index=1)
        with col2:
            offset = st.number_input("Offset", min_value=0, value=0, step=limit)

        try:
            result = client.list_items(
                type=filter_type if filter_type else None,
                status=filter_status,
                source=filter_source,
                search=search_query if search_query else None,
                limit=limit,
                offset=offset
            )

            st.caption(f"Showing {offset + 1}-{offset + len(result['items'])} of {result['total']} items")

            if result['total'] == 0:
                st.info("No items found")
            else:
                for item in result['items']:
                    render_item_card(item, key_prefix="all")

        except Exception as e:
            # Ignore RerunData exceptions (these are expected from st.rerun())
            if "RerunData" not in str(type(e).__name__):
                st.error(f"Error loading items: {e}")

    # Tab 4: Add New
    with tabs[3]:
        st.header("Add New Item")

        with st.form("add_item_form"):
            col1, col2 = st.columns(2)

            with col1:
                item_type = st.selectbox("Type", ["appointment", "meeting", "task", "goal"])
                title = st.text_input("Title *", placeholder="Enter title...")
                date_val = st.date_input("Date *", value=date.today())

            with col2:
                status = st.selectbox("Status", ["upcoming", "in_progress", "done"], index=0)
                priority = st.selectbox("Priority", [None, "low", "med", "high"], index=2)
                source = st.selectbox("Source", ["manual", "gmail", "calendar"], index=0)

            description = st.text_area("Description", placeholder="Optional description...")

            col1, col2 = st.columns(2)
            with col1:
                start_time = st.time_input("Start Time (optional)", value=None)
            with col2:
                location = st.text_input("Location (optional)")

            if st.form_submit_button("➕ Create Item"):
                if not title:
                    st.error("Title is required")
                else:
                    try:
                        new_item = {
                            "type": item_type,
                            "title": title,
                            "date": str(date_val),
                            "status": status,
                            "source": source,
                            "priority": priority,
                            "description": description if description else None,
                            "start_time": start_time.strftime("%H:%M") if start_time else None,
                            "location": location if location else None
                        }

                        created = client.create_item(new_item)
                        st.success(f"✅ Created: {created['title']}")
                        st.balloons()

                    except Exception as e:
                        st.error(f"Error creating item: {e}")


if __name__ == "__main__":
    main()
