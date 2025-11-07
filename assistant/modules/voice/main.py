"""
Voice & Chat UI (Streamlit)
===========================
Interactive chat interface connected to FastAPI backend.
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, Optional

# Backend configuration
BACKEND_URL = "http://localhost:8000"


def register(app, publish, subscribe):
    """No FastAPI routes in Phase 1; Streamlit runs separately."""
    pass


def check_backend_health() -> bool:
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=2)
        return response.status_code == 200
    except:
        return False


def parse_intent(user_input: str) -> Dict[str, Any]:
    """
    Parse user input to determine intent.
    Simple keyword-based parsing for MVP.
    """
    input_lower = user_input.lower()

    # Behavior tracking - Set goal
    if any(word in input_lower for word in ["set goal", "new goal", "goal:", "target"]):
        return {"action": "set_goal", "content": user_input}

    # Behavior tracking - Log session
    if any(word in input_lower for word in ["did gym", "did guitar", "completed", "finished session"]):
        return {"action": "log_session", "content": user_input}

    # Behavior tracking - Show goals
    if any(word in input_lower for word in ["my goals", "show goals", "list goals", "goal progress"]):
        return {"action": "show_goals"}

    # Behavior tracking - Weekly review
    if any(word in input_lower for word in ["weekly review", "week review", "how am i doing", "my progress"]):
        return {"action": "weekly_review"}

    # Behavior tracking - Adherence
    if any(word in input_lower for word in ["adherence", "how close", "on track"]):
        return {"action": "adherence"}

    # Add memory
    if any(word in input_lower for word in ["remember", "save", "note", "remind me"]):
        return {"action": "add_memory", "content": user_input}

    # Add task
    if any(word in input_lower for word in ["task", "todo", "do", "need to"]):
        return {"action": "add_task", "content": user_input}

    # List tasks
    if any(word in input_lower for word in ["show tasks", "list tasks", "my tasks", "what tasks"]):
        return {"action": "list_tasks"}

    # Email summary
    if any(word in input_lower for word in ["email", "inbox", "mail"]):
        return {"action": "email_summary"}

    # Detect events
    if any(word in input_lower for word in ["detect events", "find events", "scan for events"]):
        return {"action": "detect_events"}

    # Show events
    if any(word in input_lower for word in ["show events", "my events", "upcoming events", "pending events"]):
        return {"action": "show_events"}

    # Default: add as memory
    return {"action": "add_memory", "content": user_input}


def call_backend(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Call the appropriate backend API based on intent"""
    try:
        action = intent.get("action")

        if action == "add_memory":
            response = requests.post(
                f"{BACKEND_URL}/memory/add", json={"content": intent["content"]}, timeout=5
            )
            response.raise_for_status()
            return {"success": True, "message": f"✓ Saved to memory: {intent['content'][:50]}..."}

        elif action == "add_task":
            # Extract task details (simple for MVP - importance/urgency default to 5)
            response = requests.post(
                f"{BACKEND_URL}/tasks/add",
                json={"title": intent["content"], "urgency": 5, "importance": 5, "effort": 3},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
            return {"success": True, "message": f"✓ Added task: {data['task']['title']}"}

        elif action == "list_tasks":
            response = requests.get(f"{BACKEND_URL}/tasks/list", timeout=5)
            response.raise_for_status()
            data = response.json()
            tasks = data.get("prioritised_tasks", [])

            if not tasks:
                return {
                    "success": True,
                    "message": "No tasks yet. Add one by saying 'task: do something'",
                }

            task_list = "📋 Your Tasks (prioritized):\n\n"
            for i, (title, priority) in enumerate(tasks[:10], 1):
                task_list += f"{i}. {title} (priority: {priority:.1f})\n"

            return {"success": True, "message": task_list}

        elif action == "email_summary":
            response = requests.get(f"{BACKEND_URL}/emails/summarise", timeout=5)
            response.raise_for_status()
            data = response.json()
            return {"success": True, "message": f"📧 {data.get('summary', 'No summary available')}"}

        elif action == "detect_events":
            response = requests.get(f"{BACKEND_URL}/emails/detect-events?limit=50", timeout=10)
            response.raise_for_status()
            data = response.json()
            detected = data.get("detected", 0)
            if detected == 0:
                return {"success": True, "message": "No events detected in recent emails"}
            return {"success": True, "message": f"📅 Detected {detected} events! Use 'show events' to view them."}

        elif action == "show_events":
            response = requests.get(f"{BACKEND_URL}/emails/events?status=pending", timeout=5)
            response.raise_for_status()
            data = response.json()
            events = data.get("events", [])

            if not events:
                return {"success": True, "message": "No pending events. Use 'detect events' to scan your emails."}

            message = "📅 Detected Events (Pending Approval):\n\n"
            for event in events:
                event_type_emoji = {"meeting": "🤝", "webinar": "🎓", "deadline": "⏰", "appointment": "📍"}.get(event['event_type'], "📅")
                message += f"{event_type_emoji} **{event['title']}**\n"
                if event['date_time']:
                    message += f"   📆 {event['date_time']}\n"
                if event['location']:
                    message += f"   📍 {event['location']}\n"
                if event['url']:
                    message += f"   🔗 {event['url']}\n"
                message += f"   Confidence: {event['confidence']}\n"
                message += f"   _Event ID: {event['id']}_\n\n"

            message += "\n💡 To approve: Use calendar integration (coming soon)"
            return {"success": True, "message": message}

        elif action == "set_goal":
            # Simple goal parsing: "set goal gym 4 times per week"
            content = intent["content"].lower()
            # Extract goal name and target
            goal_name = "new goal"
            target = 4  # default

            if "gym" in content:
                goal_name = "gym"
            elif "guitar" in content:
                goal_name = "guitar practice"
            elif "reading" in content:
                goal_name = "reading"
            elif "meditation" in content:
                goal_name = "meditation"

            # Extract number
            import re
            numbers = re.findall(r'\d+', content)
            if numbers:
                target = int(numbers[0])

            response = requests.post(
                f"{BACKEND_URL}/behaviour/goals",
                json={"name": goal_name, "target_per_week": target},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return {"success": True, "message": data["message"]}

        elif action == "log_session":
            # Parse which goal: "did gym" or "completed guitar"
            content = intent["content"].lower()
            goal_name = None

            if "gym" in content:
                goal_name = "gym"
            elif "guitar" in content:
                goal_name = "guitar practice"
            elif "reading" in content:
                goal_name = "reading"
            elif "meditation" in content:
                goal_name = "meditation"

            if not goal_name:
                return {"success": False, "message": "❌ Couldn't identify which goal. Try: 'did gym' or 'completed guitar'"}

            response = requests.post(
                f"{BACKEND_URL}/behaviour/session",
                json={"goal_name": goal_name, "completed": True},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return {"success": True, "message": data["message"]}

        elif action == "show_goals":
            response = requests.get(f"{BACKEND_URL}/behaviour/goals", timeout=5)
            response.raise_for_status()
            data = response.json()
            goals = data.get("goals", [])

            if not goals:
                return {"success": True, "message": "No goals set yet. Try: 'set goal gym 4 times per week'"}

            message = "🎯 Your Goals:\n\n"
            for goal in goals:
                message += f"• {goal['name']}: {goal['completed']}/{goal['target_per_week']} completed this week\n"
            return {"success": True, "message": message}

        elif action == "adherence":
            response = requests.get(f"{BACKEND_URL}/behaviour/adherence", timeout=5)
            response.raise_for_status()
            data = response.json()
            adherence = data.get("adherence", [])

            if not adherence:
                return {"success": True, "message": "No goals tracked yet."}

            message = f"📊 Adherence Report (Week of {data['week_of']}):\n\n"
            for item in adherence:
                message += f"• {item['goal']}: {item['adherence_pct']}% ({item['completed']}/{item['target']}) {item['status']}\n"
                if item['remaining'] > 0:
                    message += f"  → {item['remaining']} sessions remaining\n"
            return {"success": True, "message": message}

        elif action == "weekly_review":
            response = requests.get(f"{BACKEND_URL}/behaviour/weekly-review", timeout=5)
            response.raise_for_status()
            data = response.json()

            summary = data.get("summary", {})
            goals_detail = data.get("goals_detail", [])
            hypotheses = data.get("hypotheses", [])

            message = f"📈 Weekly Review (Week of {data['week_of']}):\n\n"
            message += f"**Summary:**\n"
            message += f"• Total goals: {summary['total_goals']}\n"
            message += f"• On track: {summary['goals_on_track']} ✅\n"
            message += f"• Behind: {summary['goals_behind']} ⚠️\n\n"

            message += "**Goal Details:**\n"
            for goal in goals_detail:
                message += f"• {goal['goal']}: {goal['adherence_pct']}% {goal['status']}\n"

            message += "\n**Insights:**\n"
            for i, hypothesis in enumerate(hypotheses, 1):
                message += f"{i}. {hypothesis}\n"

            return {"success": True, "message": message}

        else:
            return {"success": False, "message": f"Unknown action: {action}"}

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "❌ Backend not running. Start it with: ./scripts/start.sh",
        }
    except requests.exceptions.Timeout:
        return {"success": False, "message": "❌ Request timed out. Backend may be overloaded."}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "message": f"❌ API error: {e}"}
    except Exception as e:
        return {"success": False, "message": f"❌ Unexpected error: {str(e)}"}


def streamlit_chat():
    """Main Streamlit chat interface"""
    st.set_page_config(page_title="AskSharon.ai", page_icon="🤖", layout="wide")

    st.title("🤖 AskSharon.ai")
    st.caption("Your modular personal assistant (MVP)")

    # Check backend health
    backend_status = check_backend_health()

    if backend_status:
        st.success("✓ Connected to backend")
    else:
        st.error("✗ Backend not running - Start with: ./scripts/start.sh")

    # Sidebar with help
    with st.sidebar:
        st.header("💡 How to Use")
        st.markdown(
            """
        **🎯 Behavior Tracking (NEW!):**
        - "Set goal gym 4 times per week"
        - "My goals" / "Show goals"
        - "Did gym" / "Completed guitar"
        - "How am I doing?" / "Weekly review"
        - "Show adherence" / "On track?"

        **💭 Add Memory:**
        - "Remember to buy coffee"
        - "Note: Meeting at 3pm"

        **✅ Manage Tasks:**
        - "Task: Finish report"
        - "Show my tasks"

        **📧 Check Email:**
        - "Check my email"
        - "Email summary"

        **📅 Event Detection (NEW!):**
        - "Detect events" / "Scan for events"
        - "Show events" / "My events"
        - Auto-detects: meetings, webinars, deadlines

        ---

        **Backend:** http://localhost:8000
        **API Docs:** http://localhost:8000/docs
        """
        )

        if st.button("🔄 Refresh Backend Status"):
            st.rerun()

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
        # Add welcome message
        st.session_state["messages"].append(
            (
                "Sharon",
                "👋 Hi! I'm Sharon, your personal assistant. I can help you with:\n\n"
                "🎯 **Behavior Tracking**\n"
                "  • Set goals and track progress\n"
                "  • Log completed sessions\n"
                "  • Get weekly insights\n\n"
                "💭 **Memory & Tasks**\n"
                "  • Save important notes\n"
                "  • Manage your to-dos\n\n"
                "📧 **Email & Events** (NEW!)\n"
                "  • Check your inbox\n"
                "  • Detect meetings & webinars\n"
                "  • View upcoming events\n\n"
                "Try: 'Detect events' or 'Show events'\n\n"
                "What would you like to do?",
            )
        )

    # Chat input
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.text_input(
                "Type your message:",
                placeholder="e.g., 'Remember to buy milk' or 'Show my tasks'",
                label_visibility="collapsed",
            )
        with col2:
            submit_button = st.form_submit_button("Send", use_container_width=True)

    # Process user input
    if submit_button and user_input:
        # Add user message
        st.session_state["messages"].append(("You", user_input))

        if backend_status:
            # Parse intent and call backend
            with st.spinner("Thinking..."):
                intent = parse_intent(user_input)
                result = call_backend(intent)

            # Add Sharon's response
            st.session_state["messages"].append(("Sharon", result["message"]))
        else:
            st.session_state["messages"].append(
                (
                    "Sharon",
                    "❌ I can't connect to the backend right now. Please start it with:\n"
                    "```bash\n./scripts/start.sh\n```",
                )
            )

        st.rerun()

    # Display chat history
    st.markdown("---")
    st.subheader("💬 Chat History")

    for sender, msg in st.session_state["messages"]:
        if sender == "You":
            st.markdown(f"**🧑 You:** {msg}")
        else:
            st.markdown(f"**🤖 Sharon:** {msg}")
        st.markdown("")

    # Clear chat button
    if len(st.session_state["messages"]) > 1:  # More than just welcome message
        if st.button("🗑️ Clear Chat"):
            st.session_state["messages"] = []
            st.rerun()


if __name__ == "__main__":
    streamlit_chat()
