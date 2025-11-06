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
        **Add Memory:**
        - "Remember to buy coffee"
        - "Note: Meeting at 3pm"

        **Add Task:**
        - "Task: Finish report"
        - "Need to call John"

        **List Tasks:**
        - "Show my tasks"
        - "What tasks do I have?"

        **Check Email:**
        - "Check my email"
        - "Email summary"

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
                "• Saving memories\n"
                "• Managing tasks\n"
                "• Checking emails\n"
                "• And more!\n\n"
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
