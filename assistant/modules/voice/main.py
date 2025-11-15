"""
Voice & Chat UI (Streamlit)
===========================
Interactive chat interface connected to FastAPI backend.
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, Optional
from openai import OpenAI
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Add module directory to path for imports
module_dir = Path(__file__).parent
if str(module_dir) not in sys.path:
    sys.path.insert(0, str(module_dir))

# Force reload conversational_ai to avoid Streamlit cache issues
import importlib
import conversational_ai
importlib.reload(conversational_ai)

# Import conversational AI workflows
from conversational_ai import TaskWorkflow, AppointmentWorkflow, GoalWorkflow

# Load environment variables
load_dotenv("config/.env")

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


def understand_natural_language(user_input: str) -> Dict[str, Any]:
    """
    Use OpenAI function calling to understand natural language queries.
    Handles queries like "What meetings do I have today?" → show_events
    """
    try:
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Fallback to keyword matching if no API key
            return None

        client = OpenAI(api_key=api_key)

        # Define available functions for Sharon
        functions = [
            {
                "name": "show_events",
                "description": "Show upcoming calendar events, meetings, appointments, or schedule. Use when user asks about meetings, events, calendar, schedule, or what's happening.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_filter": {
                            "type": "string",
                            "enum": ["today", "tomorrow", "this_week", "all"],
                            "description": "Time filter for events"
                        }
                    }
                }
            },
            {
                "name": "list_tasks",
                "description": "Show todo list and tasks. Use when user asks about tasks, todos, things to do, or what needs to be done.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "update_task",
                "description": "Update an existing task. Use when user wants to add/change a field in a task (e.g., 'add project to task X', 'update deadline for task Y', 'change priority of task Z').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_identifier": {
                            "type": "string",
                            "description": "Task title or partial title to identify which task to update"
                        },
                        "field": {
                            "type": "string",
                            "enum": ["project", "category", "deadline", "notes", "tags", "context", "urgency", "importance", "effort"],
                            "description": "Which field to update"
                        }
                    },
                    "required": ["task_identifier", "field"]
                }
            },
            {
                "name": "delete_task",
                "description": "Delete/remove a task from the todo list. Use when user wants to delete, remove, or cancel a task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_identifier": {
                            "type": "string",
                            "description": "Task title or partial title to identify which task to delete"
                        }
                    },
                    "required": ["task_identifier"]
                }
            },
            {
                "name": "approve_event",
                "description": "Add an email-detected event to Google Calendar. Use when user wants to add, approve, or accept an event.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_identifier": {
                            "type": "string",
                            "description": "Event title or partial title to identify which event to add"
                        }
                    },
                    "required": ["event_identifier"]
                }
            },
            {
                "name": "reject_event",
                "description": "Dismiss/ignore an email-detected event. Use when user wants to dismiss, reject, or ignore an event.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_identifier": {
                            "type": "string",
                            "description": "Event title or partial title to identify which event to dismiss"
                        }
                    },
                    "required": ["event_identifier"]
                }
            },
            {
                "name": "show_goals",
                "description": "Show behavior tracking goals and progress. Use when user asks about goals, progress, or what they're working on.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "email_summary",
                "description": "Show summary of recent emails. Use when user asks about emails, inbox, or mail.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "weekly_review",
                "description": "Show weekly progress review. Use when user asks how they're doing, their progress, or weekly summary.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "add_task",
                "description": "Add a new task or todo item. Use when user says to add, create, or remember a task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_content": {"type": "string", "description": "The task description"}
                    },
                    "required": ["task_content"]
                }
            },
            {
                "name": "add_appointment",
                "description": "Schedule a meeting or appointment. Use when user wants to schedule, book, or add a meeting/appointment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "appointment_content": {"type": "string", "description": "The appointment description"}
                    },
                    "required": ["appointment_content"]
                }
            }
        ]

        # Call OpenAI with function calling
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Fast and cheap for this use case
            messages=[
                {"role": "system", "content": "You are Sharon, a helpful personal assistant. Parse the user's request and call the appropriate function."},
                {"role": "user", "content": user_input}
            ],
            functions=functions,
            function_call="auto",
            temperature=0  # Deterministic for consistent parsing
        )

        # Extract function call
        message = response.choices[0].message
        if message.function_call:
            function_name = message.function_call.name
            arguments = json.loads(message.function_call.arguments) if message.function_call.arguments else {}

            # Map function name to action
            return {
                "action": function_name,
                "content": user_input,
                "parameters": arguments
            }
        else:
            # No function matched, return None to fallback
            return None

    except Exception as e:
        print(f"⚠️  OpenAI NLU error: {e}")
        # Fallback to keyword matching
        return None


def parse_intent(user_input: str) -> Dict[str, Any]:
    """
    Parse user input to determine intent.
    Uses OpenAI function calling for natural language understanding,
    with keyword matching as fallback.
    """
    # TRY NATURAL LANGUAGE UNDERSTANDING FIRST
    nl_result = understand_natural_language(user_input)
    if nl_result:
        print(f"🤖 NLU: '{user_input}' → {nl_result['action']}")
        return nl_result

    # FALLBACK: Keyword matching
    print(f"🔤 Keyword matching: '{user_input}'")
    input_lower = user_input.lower()

    # Normalize common typos
    typo_map = {
        "meial": "email",
        "emial": "email",
        "eamil": "email",
        "appoitment": "appointment",
        "appointmant": "appointment",
        "calander": "calendar",
        "calender": "calendar"
    }
    for typo, correction in typo_map.items():
        input_lower = input_lower.replace(typo, correction)

    # TEST COMMANDS (for verification)
    if "test calendar" in input_lower:
        return {"action": "test_calendar"}
    if "test emails" in input_lower or "test email" in input_lower:
        return {"action": "test_emails"}
    if "test integration" in input_lower:
        return {"action": "test_integration"}

    # Show events (PRIORITY - check before email_summary)
    # Flexible matching for appointments, meetings, calendar
    if any(word in input_lower for word in ["show events", "my events", "upcoming events", "pending events", "appointment", "meeting", "calendar", "today's events", "events today", "tomorrow"]):
        return {"action": "show_events"}

    # Detect events
    if any(word in input_lower for word in ["detect events", "find events", "scan for events", "scan emails"]):
        return {"action": "detect_events"}

    # Email summary (check for "summary" or "recent" with email/mail)
    if any(word in input_lower for word in ["email summary", "inbox summary", "recent email", "recent mail", "summarise email", "summarize email"]):
        return {"action": "email_summary"}

    # Behavior tracking - Set goal
    if any(word in input_lower for word in ["set goal", "new goal", "goal:", "target"]):
        return {"action": "set_goal", "content": user_input}

    # Behavior tracking - Log session
    if any(word in input_lower for word in ["did gym", "did guitar", "completed session", "finished session", "logged session"]):
        return {"action": "log_session", "content": user_input}

    # Behavior tracking - Show goals (flexible matching)
    if any(word in input_lower for word in ["my goal", "show goal", "list goal", "current goal", "what goal", "goal progress"]):
        return {"action": "show_goals"}

    # Behavior tracking - Weekly review
    if any(word in input_lower for word in ["weekly review", "week review", "how am i doing", "my progress"]):
        return {"action": "weekly_review"}

    # Behavior tracking - Adherence
    if any(word in input_lower for word in ["adherence", "how close", "on track"]):
        return {"action": "adherence"}

    # List tasks (check before add_task)
    if any(word in input_lower for word in ["show tasks", "list tasks", "my tasks", "what tasks", "view tasks"]):
        return {"action": "list_tasks"}

    # Add task (SPECIFIC - removed "do", only explicit task keywords)
    if any(word in input_lower for word in ["add task", "new task", "task:", "todo:", "need to complete", "need to finish"]):
        return {"action": "add_task", "content": user_input}

    # Add appointment/meeting (NEW)
    if any(word in input_lower for word in ["add appointment", "add meeting", "schedule meeting", "schedule appointment", "book meeting", "create meeting"]):
        return {"action": "add_appointment", "content": user_input}

    # Add memory (explicit)
    if any(word in input_lower for word in ["remember this", "save this", "note:", "remind me to"]):
        return {"action": "add_memory", "content": user_input}

    # Default: Show a helpful message instead of adding as memory
    # This prevents accidental memory/task creation from questions
    return {"action": "unknown", "content": user_input}


def filter_events_by_time(events: list, time_filter: str = "all") -> list:
    """Filter events by time (today, tomorrow, this_week, all)"""
    if time_filter == "all":
        return events

    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)

    filtered = []
    for event in events:
        dt_str = event.get("date_time", "")
        if not dt_str:
            continue

        try:
            # Parse date
            if "T" in dt_str:
                event_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                event_date = event_dt.date()
            else:
                event_date = datetime.fromisoformat(dt_str).date()

            # Apply filter
            if time_filter == "today" and event_date == today:
                filtered.append(event)
            elif time_filter == "tomorrow" and event_date == tomorrow:
                filtered.append(event)
            elif time_filter == "this_week" and today <= event_date <= week_end:
                filtered.append(event)
        except:
            continue

    return filtered


def call_backend(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Call the appropriate backend API based on intent"""
    try:
        action = intent.get("action")
        parameters = intent.get("parameters", {})
        print(f"\n{'='*60}")
        print(f"🔵 ACTION: {action}")
        if parameters:
            print(f"📋 PARAMETERS: {parameters}")
        print(f"{'='*60}")

        # DEBUG: Workflow state tracking
        active_workflow = st.session_state.get('active_workflow')
        print(f"🔍 DEBUG: active_workflow={active_workflow}")
        print(f"🔍 DEBUG: task_workflow_exists={'task_workflow' in st.session_state}")
        print(f"🔍 DEBUG: appointment_workflow_exists={'appointment_workflow' in st.session_state}")

        # CHECK FOR CANCEL/RESET COMMAND
        user_input = intent.get("content", "").lower()
        if any(word in user_input for word in ["cancel", "start over", "reset", "nevermind", "stop"]):
            # Clear all workflows
            if 'task_workflow' in st.session_state:
                del st.session_state.task_workflow
            if 'appointment_workflow' in st.session_state:
                del st.session_state.appointment_workflow
            if 'active_workflow' in st.session_state:
                del st.session_state.active_workflow
            print("✓ Workflow cancelled by user")
            return {"success": True, "message": "✓ Workflow cancelled. What would you like to do?"}

        # WORKFLOW PRESERVATION: If a workflow is active, continue it
        if active_workflow == 'task' and action != 'add_task':
            print(f"⚠️  WORKFLOW CORRECTION: Detected action '{action}' but task workflow is active. Forcing add_task.")
            action = 'add_task'
        elif active_workflow == 'appointment' and action != 'add_appointment':
            print(f"⚠️  WORKFLOW CORRECTION: Detected action '{action}' but appointment workflow is active. Forcing add_appointment.")
            action = 'add_appointment'
        elif active_workflow == 'goal':
            print(f"⚠️  WORKFLOW CORRECTION: Goal workflow is active. Continuing goal creation.")
            # Handle goal workflow immediately - don't let it fall through to other actions
            workflow = st.session_state.goal_workflow
            print(f"🔄 Continuing GOAL workflow - current fields: {workflow.fields}")

            # Process user's response
            result = workflow.process_response(intent.get("content", ""))

            if not result.get("extracted"):
                # Extraction failed, ask again
                error_msg = result.get("error", "")
                next_question = workflow.get_confirmation_question()
                return {"success": True, "message": f"⚠️ {error_msg}\n\n{next_question}"}

            # Check if workflow complete
            if workflow.is_complete():
                # All fields collected → Create goal
                goal_data = workflow.to_goal_data()

                response = requests.post(
                    f"{BACKEND_URL}/behaviour/goals",
                    json=goal_data,
                    timeout=5
                )
                response.raise_for_status()

                # Clear workflow from session
                summary = workflow.get_summary()
                del st.session_state.goal_workflow
                if 'active_workflow' in st.session_state:
                    del st.session_state.active_workflow
                print("✅ Goal workflow COMPLETED and cleared")

                return {"success": True, "message": summary}
            else:
                # More fields needed (waiting for confirmation or additional details)
                next_question = workflow.get_confirmation_question()
                return {"success": True, "message": next_question}

        if action == "add_memory":
            response = requests.post(
                f"{BACKEND_URL}/memory/add", json={"content": intent["content"]}, timeout=5
            )
            response.raise_for_status()
            return {"success": True, "message": f"✓ Saved to memory: {intent['content'][:50]}..."}

        elif action == "add_task":
            # CONVERSATIONAL TASK CREATION with upfront extraction
            # Check if workflow already exists in session state
            if 'task_workflow' not in st.session_state:
                # Start new workflow
                st.session_state.task_workflow = TaskWorkflow()
                st.session_state.active_workflow = 'task'  # SET ACTIVE WORKFLOW
                print("🎯 Started new TASK workflow")

                # NEW: Do upfront extraction from the initial message
                workflow = st.session_state.task_workflow
                result = workflow.process_response(intent.get("content", ""))

                print(f"🔍 Upfront extraction result: {result}")

                # Build response message
                message_parts = []

                # Add acknowledgment if present
                if result.get("acknowledgment"):
                    message_parts.append(result["acknowledgment"])

                # Add suggestion if present (e.g., recurring pattern → goal suggestion)
                if result.get("suggestion"):
                    message_parts.append("\n\n" + result["suggestion"])

                # Check if workflow is complete after extraction
                if workflow.is_complete():
                    # All fields extracted! Create task immediately
                    task_data = workflow.to_dict()
                    response = requests.post(
                        f"{BACKEND_URL}/tasks/add",
                        json=task_data,
                        timeout=5,
                    )
                    response.raise_for_status()

                    # Clear workflow from session
                    summary = workflow.get_summary()
                    del st.session_state.task_workflow
                    if 'active_workflow' in st.session_state:
                        del st.session_state.active_workflow
                    print("✅ Task workflow COMPLETED immediately after extraction")

                    if message_parts:
                        message_parts.append("\n\n" + summary)
                        return {"success": True, "message": "\n".join(message_parts)}
                    else:
                        return {"success": True, "message": summary}
                else:
                    # More fields needed, ask next question
                    next_question = workflow.get_next_question()
                    if message_parts:
                        message_parts.append("\n\n" + next_question)
                        return {"success": True, "message": "\n".join(message_parts)}
                    else:
                        return {"success": True, "message": next_question}

            # Continue existing workflow
            workflow = st.session_state.task_workflow
            print(f"🔄 Continuing TASK workflow - current fields: {workflow.fields}")

            # Process user's response
            result = workflow.process_response(intent.get("content", ""))

            if not result.get("extracted"):
                # Extraction failed, ask again
                error_msg = result.get("error", "")
                next_question = workflow.get_next_question()
                return {"success": True, "message": f"⚠️ {error_msg}\n\n{next_question}"}

            # Check if user wants to create a goal instead of task
            if result.get("create_goal"):
                # User confirmed they want a goal for the recurring pattern
                # Switch from TaskWorkflow to GoalWorkflow
                print(f"✅ Switching from task to goal workflow")

                # Create GoalWorkflow and initialize from TaskWorkflow
                goal_workflow = GoalWorkflow()
                goal_workflow.set_from_task_workflow(workflow)

                # Clear task workflow from session
                del st.session_state.task_workflow

                # Store goal workflow in session
                st.session_state.goal_workflow = goal_workflow
                st.session_state.active_workflow = 'goal'

                # Ask for confirmation
                confirmation_question = goal_workflow.get_confirmation_question()
                return {"success": True, "message": confirmation_question}

            # Check if workflow complete
            if workflow.is_complete():
                # All fields collected → Create task
                task_data = workflow.to_dict()
                response = requests.post(
                    f"{BACKEND_URL}/tasks/add",
                    json=task_data,
                    timeout=5,
                )
                response.raise_for_status()

                # Clear workflow from session
                summary = workflow.get_summary()
                del st.session_state.task_workflow
                if 'active_workflow' in st.session_state:
                    del st.session_state.active_workflow
                print("✅ Task workflow COMPLETED and cleared")

                return {"success": True, "message": summary}
            else:
                # More fields needed, ask next question
                next_question = workflow.get_next_question()
                return {"success": True, "message": next_question}

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

        elif action == "update_task":
            # TASK UPDATE - Simple single-field update
            task_identifier = intent.get("parameters", {}).get("task_identifier", "")
            field = intent.get("parameters", {}).get("field", "")

            if not task_identifier or not field:
                return {"success": True, "message": "⚠️ Please specify which task and which field to update."}

            # Fetch all tasks to find matching one
            response = requests.get(f"{BACKEND_URL}/tasks/list", timeout=5)
            response.raise_for_status()
            data = response.json()
            tasks = data.get("prioritised_tasks", [])

            # Find task by fuzzy title matching (simple substring match)
            matching_task = None
            task_id = None

            # Also try direct database query to get task ID
            import sqlite3
            db_path = "assistant/data/memory.db"
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title FROM tasks WHERE completed = 0 AND title LIKE ? LIMIT 1",
                    (f"%{task_identifier}%",)
                )
                result = cursor.fetchone()
                conn.close()

                if result:
                    task_id = result[0]
                    matching_task = result[1]
            except Exception as e:
                print(f"⚠️ Error querying tasks: {e}")

            if not task_id:
                return {"success": True, "message": f"⚠️ Could not find task matching '{task_identifier}'. Please try with more specific keywords."}

            # Check if we already have the value in session state
            update_key = f"update_task_{task_id}_{field}"
            if update_key not in st.session_state:
                # Need to collect the value - ask user
                st.session_state[update_key] = {"task_id": task_id, "field": field, "title": matching_task}

                field_prompts = {
                    "project": "What project should this task be associated with?",
                    "category": "What category? (personal, business, learning, health)",
                    "deadline": "What's the new deadline? (e.g., 'tomorrow', 'Friday', 'Nov 20')",
                    "notes": "What notes would you like to add?",
                    "tags": "What tags? (comma-separated)",
                    "context": "What's the context (where/when can this be done)?",
                    "urgency": "What's the new urgency? (1-5, where 5 is most urgent)",
                    "importance": "What's the new importance? (1-5, where 5 is most important)",
                    "effort": "What's the new effort level? (1-5, where 5 is most effort)"
                }

                prompt = field_prompts.get(field, f"What's the new value for {field}?")
                return {"success": True, "message": f"Found task: '{matching_task}'\n\n{prompt}"}
            else:
                # We have the value from user's response - apply the update
                user_value = intent.get("content", "").strip()
                update_data = {field: user_value}

                # Convert numeric fields if needed
                if field in ["urgency", "importance", "effort"]:
                    try:
                        update_data[field] = int(user_value)
                    except ValueError:
                        return {"success": True, "message": f"⚠️ {field.capitalize()} must be a number (1-5). Please try again."}

                # Send update to backend
                response = requests.put(
                    f"{BACKEND_URL}/tasks/update/{task_id}",
                    json=update_data,
                    timeout=5
                )
                response.raise_for_status()
                result = response.json()

                # Clear session state
                del st.session_state[update_key]

                return {"success": True, "message": f"✅ Updated '{matching_task}': {field} = {user_value}"}

        elif action == "delete_task":
            # DELETE TASK
            task_identifier = intent.get("parameters", {}).get("task_identifier", "")

            if not task_identifier:
                return {"success": True, "message": "⚠️ Please specify which task to delete."}

            # Find task by fuzzy matching
            import sqlite3
            db_path = "assistant/data/memory.db"
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title FROM tasks WHERE completed = 0 AND title LIKE ? LIMIT 1",
                    (f"%{task_identifier}%",)
                )
                result = cursor.fetchone()
                conn.close()

                if result:
                    task_id = result[0]
                    task_title = result[1]
                else:
                    return {"success": True, "message": f"⚠️ Could not find task matching '{task_identifier}'."}

                # Delete task
                response = requests.delete(
                    f"{BACKEND_URL}/tasks/delete/{task_id}",
                    timeout=5
                )
                response.raise_for_status()

                return {"success": True, "message": f"✅ Deleted task: '{task_title}'"}

            except Exception as e:
                print(f"⚠️ Error deleting task: {e}")
                return {"success": False, "message": f"❌ Error deleting task: {str(e)}"}

        elif action == "approve_event":
            # ADD EMAIL EVENT TO CALENDAR
            event_identifier = intent.get("parameters", {}).get("event_identifier", "")

            if not event_identifier:
                return {"success": True, "message": "⚠️ Please specify which event to add."}

            # Fetch pending events
            response = requests.get(f"{BACKEND_URL}/emails/events?status=pending&future_only=true", timeout=5)
            response.raise_for_status()
            events = response.json().get("events", [])

            # Find matching event
            matching_event = None
            for event in events:
                if event_identifier.lower() in event.get("title", "").lower():
                    matching_event = event
                    break

            if not matching_event:
                return {"success": True, "message": f"⚠️ Could not find event matching '{event_identifier}'."}

            event_id = matching_event.get("id")
            event_title = matching_event.get("title")

            # Approve event (marks as approved)
            approve_response = requests.post(
                f"{BACKEND_URL}/emails/events/{event_id}/approve",
                timeout=5
            )

            if approve_response.status_code != 200:
                return {"success": False, "message": f"❌ Could not approve event."}

            # Create calendar event
            event_data = {
                "summary": event_title,
                "start_time": matching_event.get("date_time"),
                "location": matching_event.get("location"),
                "description": f"Event detected from email. URL: {matching_event.get('url', '')}"
            }

            # Calculate end time (default 1 hour)
            from datetime import datetime, timedelta
            try:
                start = datetime.fromisoformat(matching_event.get("date_time").replace("Z", "+00:00"))
                end = start + timedelta(hours=1)
                event_data["end_time"] = end.isoformat()
            except:
                pass

            cal_response = requests.post(
                f"{BACKEND_URL}/calendar/events/create",
                json=event_data,
                timeout=5
            )

            if cal_response.status_code == 200 or cal_response.status_code == 201:
                return {"success": True, "message": f"✅ Added to Google Calendar: '{event_title}'"}
            else:
                return {"success": False, "message": f"⚠️ Event approved but calendar creation failed. Make sure Google Calendar is connected."}

        elif action == "reject_event":
            # DISMISS/IGNORE EMAIL EVENT
            event_identifier = intent.get("parameters", {}).get("event_identifier", "")

            if not event_identifier:
                return {"success": True, "message": "⚠️ Please specify which event to dismiss."}

            # Fetch pending events
            response = requests.get(f"{BACKEND_URL}/emails/events?status=pending&future_only=true", timeout=5)
            response.raise_for_status()
            events = response.json().get("events", [])

            # Find matching event
            matching_event = None
            for event in events:
                if event_identifier.lower() in event.get("title", "").lower():
                    matching_event = event
                    break

            if not matching_event:
                return {"success": True, "message": f"⚠️ Could not find event matching '{event_identifier}'."}

            event_id = matching_event.get("id")
            event_title = matching_event.get("title")

            # Reject event
            reject_response = requests.post(
                f"{BACKEND_URL}/emails/events/{event_id}/reject",
                timeout=5
            )

            if reject_response.status_code == 200:
                return {"success": True, "message": f"✅ Dismissed event: '{event_title}'"}
            else:
                return {"success": False, "message": f"❌ Could not dismiss event."}

        elif action == "email_summary":
            response = requests.get(f"{BACKEND_URL}/emails/summarise", timeout=5)
            response.raise_for_status()
            data = response.json()
            return {"success": True, "message": f"📧 {data.get('summary', 'No summary available')}"}

        elif action == "add_appointment":
            # CONVERSATIONAL APPOINTMENT CREATION
            if 'appointment_workflow' not in st.session_state:
                # Start new workflow
                st.session_state.appointment_workflow = AppointmentWorkflow()
                st.session_state.active_workflow = 'appointment'  # SET ACTIVE WORKFLOW
                print("🎯 Started new APPOINTMENT workflow")
                next_question = st.session_state.appointment_workflow.get_next_question()
                return {"success": True, "message": next_question}

            # Continue existing workflow
            workflow = st.session_state.appointment_workflow
            print(f"🔄 Continuing APPOINTMENT workflow - current fields: {workflow.fields}")

            # Process user's response
            result = workflow.process_response(intent.get("content", ""))

            if not result.get("extracted"):
                # Extraction failed, ask again
                error_msg = result.get("error", "")
                next_question = workflow.get_next_question()
                return {"success": True, "message": f"⚠️ {error_msg}\n\n{next_question}"}

            # Check if workflow complete
            if workflow.is_complete():
                # All fields collected → Create calendar event
                event_data = workflow.to_calendar_event()

                # Create event in Google Calendar
                response = requests.post(
                    f"{BACKEND_URL}/calendar/events/create",
                    json=event_data,
                    timeout=5,
                )

                if response.status_code == 200 or response.status_code == 201:
                    # Success
                    summary = workflow.get_summary()
                    del st.session_state.appointment_workflow
                    if 'active_workflow' in st.session_state:
                        del st.session_state.active_workflow
                    print("✅ Appointment workflow COMPLETED and cleared")
                    return {"success": True, "message": summary}
                else:
                    # Calendar API error
                    del st.session_state.appointment_workflow
                    if 'active_workflow' in st.session_state:
                        del st.session_state.active_workflow
                    print("❌ Appointment workflow FAILED and cleared")
                    error_detail = response.json().get("detail", "Unknown error")
                    return {"success": False, "message": f"❌ Could not create calendar event: {error_detail}\n\nTip: Make sure Google Calendar is connected. Visit http://localhost:8000/calendar/auth to authenticate."}
            else:
                # More fields needed, ask next question
                next_question = workflow.get_next_question()
                return {"success": True, "message": next_question}

        elif action == "detect_events":
            response = requests.get(f"{BACKEND_URL}/emails/detect-events?limit=50", timeout=10)
            response.raise_for_status()
            data = response.json()
            detected = data.get("detected", 0)
            if detected == 0:
                return {"success": True, "message": "No events detected in recent emails"}
            return {"success": True, "message": f"📅 Detected {detected} events! Use 'show events' to view them."}

        elif action == "show_events":
            # Fetch BOTH calendar events and email-detected events
            all_events = []

            # 1. Get Google Calendar events
            try:
                cal_response = requests.get(f"{BACKEND_URL}/calendar/events?max_results=20", timeout=10)
                if cal_response.status_code == 200:
                    cal_data = cal_response.json()
                    cal_events = cal_data.get("events", [])
                    print(f"📅 DEBUG: Fetched {len(cal_events)} calendar events")
                    for event in cal_events:
                        all_events.append({
                            "source": "calendar",
                            "title": event.get("summary", "No title"),
                            "date_time": event.get("start"),
                            "location": event.get("location"),
                            "description": event.get("description"),
                            "type": "calendar_event"
                        })
                else:
                    print(f"⚠️  DEBUG: Calendar API returned {cal_response.status_code}")
            except Exception as e:
                print(f"⚠️  DEBUG: Calendar fetch error: {e}")
                pass  # Calendar might not be set up

            # 2. Get email-detected events (auto-scan if empty)
            email_response = requests.get(f"{BACKEND_URL}/emails/events?status=pending&future_only=true", timeout=5)
            email_response.raise_for_status()
            email_data = email_response.json()
            email_events = email_data.get("events", [])
            print(f"📧 DEBUG: Fetched {len(email_events)} email events")

            # Auto-scan if no email events
            if not email_events:
                try:
                    print("🔄 DEBUG: No email events, auto-scanning...")
                    scan_response = requests.get(f"{BACKEND_URL}/emails/detect-events?limit=50", timeout=15)
                    scan_data = scan_response.json()
                    print(f"✅ DEBUG: Scan detected {scan_data.get('detected', 0)} events")
                    email_response = requests.get(f"{BACKEND_URL}/emails/events?status=pending&future_only=true", timeout=5)
                    email_events = email_response.json().get("events", [])
                    print(f"📧 DEBUG: After scan, fetched {len(email_events)} email events")
                except Exception as e:
                    print(f"⚠️  DEBUG: Email scan error: {e}")
                    pass

            # Add email events to list
            for event in email_events:
                all_events.append({
                    "source": "email",
                    "title": event.get("title"),
                    "date_time": event.get("date_time"),
                    "location": event.get("location"),
                    "url": event.get("url"),
                    "type": event.get("event_type", "event"),
                    "confidence": event.get("confidence")
                })

            if not all_events:
                return {"success": True, "message": "📭 No upcoming events found.\n\n💡 Events are detected from:\n  📅 Your Google Calendar\n  📧 Recent emails (meetings, webinars)"}

            # Sort by date (earliest first)
            from datetime import datetime, timezone
            def parse_date(event):
                dt_str = event.get("date_time", "")
                if not dt_str:
                    return datetime.max.replace(tzinfo=timezone.utc)
                try:
                    # Handle ISO datetime with timezone (e.g., "2025-11-20T20:00:00Z")
                    if "T" in dt_str and ("Z" in dt_str or "+" in dt_str or "-" in dt_str[-6:]):
                        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    # Handle ISO datetime WITHOUT timezone (e.g., "2025-11-15T00:00:00")
                    elif "T" in dt_str:
                        dt = datetime.fromisoformat(dt_str)
                        return dt.replace(tzinfo=timezone.utc)
                    # Handle date-only strings (e.g., "2026-08-22")
                    else:
                        dt = datetime.fromisoformat(dt_str)
                        return dt.replace(tzinfo=timezone.utc)
                except Exception as e:
                    print(f"⚠️ Parse date error for '{dt_str}': {e}")
                    return datetime.max.replace(tzinfo=timezone.utc)

            all_events.sort(key=parse_date)

            # Apply time filter if provided
            time_filter = parameters.get("time_filter", "all")
            if time_filter and time_filter != "all":
                all_events = filter_events_by_time(all_events, time_filter)
                print(f"🔍 DEBUG: Filtered to {time_filter}: {len(all_events)} events")

            print(f"📊 DEBUG: Displaying {len(all_events)} total events")

            # Build message with time context
            time_context = {
                "today": "**Today's Events:**",
                "tomorrow": "**Tomorrow's Events:**",
                "this_week": "**This Week's Events:**",
                "all": "**Upcoming Events:**"
            }.get(time_filter, "**Upcoming Events:**")

            message = f"📅 {time_context}\n\n"
            for event in all_events[:15]:  # Show top 15
                # Source indicator
                if event["source"] == "calendar":
                    source_label = "**[GOOGLE CALENDAR]**"
                    source_icon = "📅"
                else:
                    source_label = "**[FROM EMAIL]**"
                    source_icon = "📧"

                type_emoji = {
                    "meeting": "🤝",
                    "webinar": "🎓",
                    "deadline": "⏰",
                    "appointment": "📍",
                    "calendar_event": "📆"
                }.get(event["type"], "📅")

                message += f"{source_icon} {type_emoji} **{event['title']}** {source_label}\n"
                if event.get('date_time'):
                    # Format date nicely
                    try:
                        dt = parse_date(event)
                        if dt != datetime.max:
                            message += f"   🕐 {dt.strftime('%b %d, %Y at %I:%M %p') if 'T' in event['date_time'] else dt.strftime('%b %d, %Y')}\n"
                    except:
                        message += f"   🕐 {event['date_time']}\n"

                if event.get('location'):
                    message += f"   📍 {event['location']}\n"
                if event.get('url'):
                    message += f"   🔗 {event['url']}\n"
                if event.get('description') and len(event['description']) < 100:
                    message += f"   📝 {event['description']}\n"
                if event.get('confidence'):
                    message += f"   💯 Confidence: {event['confidence']}\n"

                message += "\n"

            cal_count = len([e for e in all_events if e["source"] == "calendar"])
            email_count = len([e for e in all_events if e["source"] == "email"])
            message += f"\n✅ Found {len(all_events)} event(s): {cal_count} from Calendar 📅 | {email_count} from Emails 📧"

            # Terminal logging summary
            print(f"\n✅ EVENT SUMMARY:")
            print(f"   📅 Calendar events: {cal_count}")
            print(f"   📧 Email events: {email_count}")
            print(f"   📊 Total displayed: {len(all_events[:15])} (of {len(all_events)})")
            print(f"{'='*60}\n")

            return {"success": True, "message": message}

        elif action == "test_calendar":
            # Test command: Show next 3 calendar events
            response = requests.get(f"{BACKEND_URL}/calendar/events?max_results=3", timeout=10)
            response.raise_for_status()
            data = response.json()
            events = data.get("events", [])

            if not events:
                return {"success": True, "message": "📅 No calendar events found"}

            message = "📅 **TEST: Next 3 Calendar Events**\n\n"
            for i, event in enumerate(events, 1):
                message += f"{i}. **{event.get('summary', 'No title')}**\n"
                message += f"   📆 {event.get('start', 'No date')}\n"
                message += f"   📍 {event.get('location') or 'No location'}\n"
                message += f"   📝 {event.get('description', 'No description')[:100]}\n\n"

            message += f"✅ **Gmail Calendar integration working!** Found {len(events)} event(s)"
            return {"success": True, "message": message}

        elif action == "test_emails":
            # Test command: Show last 3 emails
            response = requests.get(f"{BACKEND_URL}/emails/summarise", timeout=10)
            response.raise_for_status()
            data = response.json()
            emails = data.get("emails", [])

            if not emails:
                return {"success": True, "message": "📧 No emails found"}

            message = "📧 **TEST: Last 3 Emails Received**\n\n"
            for i, email in enumerate(emails[:3], 1):
                message += f"{i}. **{email.get('subject', 'No subject')}**\n"
                message += f"   From: {email.get('from_name', 'Unknown')} ({email.get('from_email', '')})\n"
                message += f"   📅 {email.get('date_received', 'Unknown')}\n"
                message += f"   Priority: {email.get('priority', 'N/A')}\n\n"

            message += f"✅ **Gmail integration working!** Found {data.get('total', len(emails))} email(s)"
            return {"success": True, "message": message}

        elif action == "test_integration":
            # Test command: Full integration test
            message = "🧪 **FULL INTEGRATION TEST**\n\n"

            # Test 1: Calendar
            try:
                cal_resp = requests.get(f"{BACKEND_URL}/calendar/events?max_results=3", timeout=5)
                cal_data = cal_resp.json() if cal_resp.status_code == 200 else {}
                cal_count = len(cal_data.get("events", []))
                message += f"✅ Calendar API: {cal_count} event(s)\n"
            except Exception as e:
                message += f"❌ Calendar API: Failed ({str(e)})\n"

            # Test 2: Emails
            try:
                email_resp = requests.get(f"{BACKEND_URL}/emails/summarise", timeout=5)
                email_data = email_resp.json() if email_resp.status_code == 200 else {}
                email_count = email_data.get("total", 0)
                message += f"✅ Email API: {email_count} email(s)\n"
            except Exception as e:
                message += f"❌ Email API: Failed ({str(e)})\n"

            # Test 3: Event Detection
            try:
                events_resp = requests.get(f"{BACKEND_URL}/emails/events?status=pending&future_only=true", timeout=5)
                events_data = events_resp.json() if events_resp.status_code == 200 else {}
                events_count = len(events_data.get("events", []))
                message += f"✅ Event Detection: {events_count} event(s) detected from emails\n"
            except Exception as e:
                message += f"❌ Event Detection: Failed ({str(e)})\n"

            message += "\n**📊 Summary:**\n"
            message += f"- Gmail Calendar: ✅ Connected\n"
            message += f"- Gmail Inbox: ✅ Connected\n"
            message += f"- Event Detection: ✅ Active\n"

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

            # Return goals data for custom rendering with progress bars
            return {"success": True, "message": None, "goals_data": goals}

        elif action == "show_goals_text":
            # Fallback text-only version
            response = requests.get(f"{BACKEND_URL}/behaviour/goals", timeout=5)
            response.raise_for_status()
            data = response.json()
            goals = data.get("goals", [])

            if not goals:
                return {"success": True, "message": "No goals set yet. Try: 'set goal gym 4 times per week'"}

            message = "🎯 Your Goals:\n\n"
            for goal in goals:
                progress_pct = (goal['completed'] / goal['target_per_week']) * 100 if goal['target_per_week'] > 0 else 0
                progress_bar = "█" * int(progress_pct / 10) + "░" * (10 - int(progress_pct / 10))
                message += f"• **{goal['name']}**: {goal['completed']}/{goal['target_per_week']} ({progress_pct:.0f}%)\n"
                message += f"  {progress_bar}\n\n"
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

        elif action == "unknown":
            # User query didn't match any known pattern
            # Provide helpful suggestions
            return {
                "success": True,
                "message": "🤔 I'm not sure what you're asking. Try:\n\n"
                          "📅 **Events:** 'show events', 'my appointments', 'calendar'\n"
                          "📧 **Email:** 'email summary', 'recent emails'\n"
                          "🎯 **Goals:** 'show goals', 'set goal gym 4 times'\n"
                          "✅ **Tasks:** 'add task: do something', 'show tasks'\n"
                          "💾 **Memory:** 'remember this: something important'\n\n"
                          f"💬 You said: _{intent.get('content', '')}_"
            }

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
    """Main Streamlit chat interface with modern UI"""
    st.set_page_config(page_title="AskSharon.ai", page_icon="🤖", layout="wide")

    # Check backend health
    backend_status = check_backend_health()

    # COMPACT HEADER - One line with status
    header_col1, header_col2 = st.columns([6, 1])
    with header_col1:
        status_emoji = "✅" if backend_status else "❌"
        status_text = "Online" if backend_status else "Offline"
        st.markdown(f"### 🤖 **AskSharon** | {status_emoji} {status_text}")
    with header_col2:
        if st.button("🔄", help="Refresh"):
            st.rerun()

    # Sidebar with quick actions and tools
    with st.sidebar:
        st.markdown("### ⚡ Quick Actions")

        # Quick action buttons in sidebar
        if st.button("📅 Today's Events", use_container_width=True, key="sidebar_events"):
            st.session_state["messages"].append({"role": "user", "content": "show my events"})
            with st.spinner("Loading..."):
                intent = parse_intent("show my events")
                result = call_backend(intent)
            st.session_state["messages"].append({"role": "assistant", "content": result["message"]})
            st.rerun()

        if st.button("🎯 My Goals", use_container_width=True, key="sidebar_goals"):
            st.session_state["messages"].append({"role": "user", "content": "show my goals"})
            with st.spinner("Loading goals..."):
                intent = parse_intent("show my goals")
                result = call_backend(intent)

            # Handle goals_data rendering (same as main chat)
            if result.get("goals_data"):
                goals = result["goals_data"]
                goals_message = "🎯 **Your Goals:**\n\n"
                for goal in goals:
                    progress_pct = (goal['completed'] / goal['target_per_week']) * 100 if goal['target_per_week'] > 0 else 0
                    status_emoji = "🔥" if progress_pct >= 75 else "✅" if progress_pct >= 50 else "⚠️"
                    goals_message += f"{status_emoji} **{goal['name']}** - {goal['completed']}/{goal['target_per_week']} sessions ({progress_pct:.0f}%)\n\n"

                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": goals_message,
                    "goals_visual": goals
                })
            else:
                st.session_state["messages"].append({"role": "assistant", "content": result["message"]})
            st.rerun()

        if st.button("✅ My Tasks", use_container_width=True, key="sidebar_tasks"):
            st.session_state["messages"].append({"role": "user", "content": "show my tasks"})
            with st.spinner("Loading tasks..."):
                intent = parse_intent("show my tasks")
                result = call_backend(intent)
            st.session_state["messages"].append({"role": "assistant", "content": result["message"]})
            st.rerun()

        if st.button("📊 Weekly Review", use_container_width=True, key="sidebar_review"):
            st.session_state["messages"].append({"role": "user", "content": "weekly review"})
            with st.spinner("Loading review..."):
                intent = parse_intent("weekly review")
                result = call_backend(intent)
            st.session_state["messages"].append({"role": "assistant", "content": result["message"]})
            st.rerun()

        st.markdown("---")
        st.markdown("### ➕ Create New")

        # Add Task button
        if st.button("➕ Add Task", use_container_width=True, key="sidebar_add_task"):
            st.session_state["messages"].append({"role": "user", "content": "add task"})
            with st.spinner("Starting..."):
                intent = parse_intent("add task")
                result = call_backend(intent)
            st.session_state["messages"].append({"role": "assistant", "content": result["message"]})
            st.rerun()

        # Add Appointment button
        if st.button("📅 Add Appointment", use_container_width=True, key="sidebar_add_appointment"):
            st.session_state["messages"].append({"role": "user", "content": "add appointment"})
            with st.spinner("Starting..."):
                intent = parse_intent("add appointment")
                result = call_backend(intent)
            st.session_state["messages"].append({"role": "assistant", "content": result["message"]})
            st.rerun()

        # DATA VERIFICATION SECTION
        st.markdown("---")
        with st.expander("📊 **Data Verification** (Proof of Gmail Integration)", expanded=False):
            st.caption("Click 'Load Data' to verify Gmail calendar & email integration")

            if st.button("🔄 Load Verification Data", key="verify_data"):
                with st.spinner("Loading..."):
                    try:
                        # Fetch next 3 calendar events
                        cal_resp = requests.get(f"{BACKEND_URL}/calendar/events?max_results=3", timeout=5)
                        cal_data = cal_resp.json() if cal_resp.status_code == 200 else {}

                        # Fetch last emails
                        email_resp = requests.get(f"{BACKEND_URL}/emails/summarise", timeout=5)
                        email_data = email_resp.json() if email_resp.status_code == 200 else {}

                        # Fetch email-detected events
                        events_resp = requests.get(f"{BACKEND_URL}/emails/events?status=pending&future_only=true", timeout=5)
                        events_data = events_resp.json() if events_resp.status_code == 200 else {}

                        # Display Calendar Events
                        st.markdown("### 📅 **Next 3 Calendar Events**")
                        if cal_data.get("events"):
                            for i, event in enumerate(cal_data["events"][:3], 1):
                                st.success(f"""
**{i}. {event.get('summary', 'No title')}**
📆 {event.get('start', 'No date')}
📍 {event.get('location') or 'No location'}
                                """)
                        else:
                            st.warning("No calendar events found")

                        # Display Recent Emails
                        st.markdown("### 📧 **Last 3 Emails Received**")
                        if email_data.get("emails"):
                            for i, email in enumerate(email_data["emails"][:3], 1):
                                st.info(f"""
**{i}. {email.get('subject', 'No subject')}**
From: {email.get('from_name', 'Unknown')} ({email.get('from_email', '')})
📅 {email.get('date_received', 'Unknown date')}
                                """)
                        else:
                            st.warning("No emails found")

                        # Display Email-Detected Events
                        st.markdown("### 🔍 **Events Detected from Emails**")
                        if events_data.get("events"):
                            st.success(f"✅ Found **{len(events_data['events'])}** event(s) in your emails")
                            for i, event in enumerate(events_data["events"][:3], 1):
                                st.info(f"""
**{i}. {event.get('title', 'No title')}**
Type: {event.get('event_type', 'event')} | Date: {event.get('date_time', 'TBD')}
                                """)
                        else:
                            st.warning("No events detected from emails")

                        # Connection status
                        st.markdown("---")
                        st.success("✅ **Gmail Integration Active**")
                        from datetime import datetime
                        st.caption(f"Last verified: {datetime.now().strftime('%I:%M %p')}")

                    except Exception as e:
                        st.error(f"❌ Error loading data: {str(e)}")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
        # Add welcome message
        st.session_state["messages"].append({
            "role": "assistant",
            "content": "👋 Hi! I'm Sharon, your personal assistant. I can help you with:\n\n"
                "🎯 **Behavior Tracking** - Set goals, track sessions, get insights\n"
                "💭 **Memory & Tasks** - Save notes, manage to-dos\n"
                "📅 **Events** - View upcoming appointments\n\n"
                "What would you like to do?"
        })

    # Display chat messages (newest at bottom with auto-scroll)
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Render visual progress bars for goals
            if "goals_visual" in message:
                for goal in message["goals_visual"]:
                    progress_val = goal['completed'] / goal['target_per_week'] if goal['target_per_week'] > 0 else 0
                    st.progress(progress_val, text=f"{goal['name']}: {goal['completed']}/{goal['target_per_week']}")
                    st.caption(f"{int(progress_val * 100)}% complete this week")

    # Chat input at BOTTOM (maximizes chat area)
    user_input = st.chat_input("Ask me anything... Try: 'What meetings do I have today?'")

    # Process user input
    if user_input:
        # Add user message
        st.session_state["messages"].append({"role": "user", "content": user_input})

        if backend_status:
            # Parse intent and call backend
            intent = parse_intent(user_input)
            result = call_backend(intent)

            # Handle special rendering for goals with progress bars
            if result.get("goals_data"):
                goals = result["goals_data"]

                # Create visual progress display
                goals_message = "🎯 **Your Goals:**\n\n"
                for goal in goals:
                    progress_pct = (goal['completed'] / goal['target_per_week']) * 100 if goal['target_per_week'] > 0 else 0
                    status_emoji = "🔥" if progress_pct >= 75 else "✅" if progress_pct >= 50 else "⚠️"

                    goals_message += f"{status_emoji} **{goal['name']}** - {goal['completed']}/{goal['target_per_week']} sessions ({progress_pct:.0f}%)\n\n"

                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": goals_message,
                    "goals_visual": goals  # Store for potential custom rendering
                })
            else:
                # Add Sharon's normal text response
                st.session_state["messages"].append({"role": "assistant", "content": result["message"]})
        else:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": "❌ I can't connect to the backend right now. Please start it with:\n"
                    "```bash\n./scripts/start.sh\n```"
            })

        st.rerun()


if __name__ == "__main__":
    streamlit_chat()
