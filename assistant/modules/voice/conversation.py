"""
Conversational AI Logic
=======================
Process user messages and determine appropriate responses/actions.
Uses LLM (OpenAI) when available, falls back to regex-based parsing.
"""

import os
import streamlit as st
from parsers import (
    parse_days, parse_time_range, format_days_list, format_time,
    extract_item_details, DAY_NAMES
)

# Check if LLM is enabled
LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() == "true"


def process_chat_message(message: str, conversation_history: list = None) -> dict:
    """Process user chat message and return structured response.

    Uses LLM (OpenAI) when available and enabled, falls back to regex parsing.
    """
    if conversation_history is None:
        conversation_history = []

    response = {
        'action': 'unknown',
        'response_text': '',
        'needs_confirmation': False,
        'pending_data': None,
        'view': None,
    }

    # PRIORITY 1: Handle confirmation responses (check BEFORE LLM to avoid delays)
    if st.session_state.get('awaiting_confirmation'):
        message_lower = message.lower().strip()
        if message_lower in ['yes', 'y', 'yeah', 'yep', 'confirm', 'ok', 'okay', 'sure', 'go ahead', 'do it', 'yes please']:
            response['action'] = 'confirm_yes'
            return response
        elif message_lower in ['no', 'n', 'nope', 'cancel', 'nevermind', 'never mind', 'stop']:
            response['action'] = 'confirm_no'
            return response
        # If not a clear yes/no, let LLM or regex handle it

    # PRIORITY 2: Try LLM processing if enabled and not in a guided flow
    if LLM_ENABLED and not st.session_state.get('goal_creation_stage'):
        try:
            from llm_processor import process_with_llm, is_configured
            if is_configured():
                pending_context = st.session_state.get('pending_goal', {})
                if st.session_state.get('awaiting_confirmation'):
                    pending_context['awaiting_confirmation'] = True
                    pending_context['pending_action'] = st.session_state.get('pending_action')

                result = process_with_llm(message, conversation_history, pending_context)

                # If LLM returned a valid action, use it
                if result.get('action') not in ['error', 'llm_not_configured', 'unknown']:
                    return result
        except ImportError:
            pass  # LLM processor not available, use regex
        except Exception as e:
            print(f"LLM processing error, falling back to regex: {e}")

    # PRIORITY 3: Fallback to regex-based parsing
    details = extract_item_details(message)

    # Handle guided goal creation flow (regex fallback)
    if st.session_state.get('goal_creation_stage'):
        message_lower = message.lower().strip()
        if message_lower in ['yes', 'y', 'yeah', 'yep', 'confirm', 'ok', 'okay', 'sure', 'go ahead']:
            response['action'] = 'confirm_yes'
            return response
        elif message_lower in ['no', 'n', 'nope', 'cancel', 'nevermind', 'never mind']:
            response['action'] = 'confirm_no'
            return response

    # Handle guided goal creation flow
    if st.session_state.get('goal_creation_stage'):
        stage = st.session_state.goal_creation_stage
        pending_goal = st.session_state.get('pending_goal', {})
        message_lower = message.lower().strip()

        if stage == 'ask_calendar':
            # User answering: "Would you like to block time?"
            if message_lower in ['yes', 'y', 'yeah', 'yep', 'sure']:
                st.session_state.goal_creation_stage = 'get_time'
                response['action'] = 'goal_flow_continue'
                response['response_text'] = "What days and time? (e.g., 'weekdays 7:30-9am' or 'mon wed fri 9-10am')"
                return response
            elif message_lower in ['no', 'n', 'nope', 'skip']:
                st.session_state.goal_creation_stage = 'get_name'
                response['action'] = 'goal_flow_continue'
                response['response_text'] = "Ok, no calendar blocking. What should I call this goal?"
                return response
            else:
                response['action'] = 'goal_flow_continue'
                response['response_text'] = "Would you like to block time in your calendar? (yes/no)"
                return response

        elif stage == 'get_time':
            # User providing time/days
            days = parse_days(message)
            start_time, end_time = parse_time_range(message)
            if days and start_time:
                pending_goal['days'] = days
                pending_goal['start_time'] = start_time
                pending_goal['end_time'] = end_time or start_time
                st.session_state.pending_goal = pending_goal
                st.session_state.goal_creation_stage = 'get_name'
                response['action'] = 'goal_flow_continue'
                days_str = format_days_list(days)
                response['response_text'] = f"Got it - {days_str} from {format_time(start_time)} to {format_time(end_time)}. What should I call this goal?"
                return response
            else:
                response['action'] = 'goal_flow_continue'
                response['response_text'] = "I didn't catch that. Please specify days and time (e.g., 'weekdays except wednesday 7:30-9am')"
                return response

        elif stage == 'get_name':
            # User providing goal name
            pending_goal['title'] = message.strip()
            st.session_state.pending_goal = pending_goal
            st.session_state.goal_creation_stage = 'get_category'
            response['action'] = 'goal_flow_continue'
            response['response_text'] = "What category is this goal? (educational, fitness, work, personal, creative, other)"
            return response

        elif stage == 'get_category':
            # User providing category
            valid_categories = ['educational', 'fitness', 'work', 'personal', 'creative', 'other']
            category = message_lower.strip()
            if category not in valid_categories:
                # Try to match partial
                for cat in valid_categories:
                    if cat.startswith(category) or category in cat:
                        category = cat
                        break
                else:
                    category = 'other'
            pending_goal['category'] = category
            st.session_state.pending_goal = pending_goal
            st.session_state.goal_creation_stage = None

            # Build confirmation
            title = pending_goal.get('title', 'Untitled').title()
            if pending_goal.get('days'):
                days_str = format_days_list(pending_goal['days'])
                time_str = f"{format_time(pending_goal['start_time'])} to {format_time(pending_goal['end_time'])}"
                response['response_text'] = f"I'll create goal **'{title}'** ({category}) with sessions on **{days_str}** from **{time_str}** and add them to your Google Calendar. Confirm?"
                response['action'] = 'create_goal_with_sessions'
            else:
                response['response_text'] = f"I'll create goal **'{title}'** ({category}). Confirm?"
                response['action'] = 'create_goal'

            response['needs_confirmation'] = True
            response['pending_data'] = pending_goal
            return response

    # Handle multi-turn conversation - waiting for more info (legacy)
    if st.session_state.get('awaiting_info'):
        awaiting_type = st.session_state.get('awaiting_info_type')
        if awaiting_type == 'goal_name':
            goal_name = message.strip()
            st.session_state.awaiting_info = False
            st.session_state.awaiting_info_type = None
            response['action'] = 'create_goal'
            response['needs_confirmation'] = True
            response['pending_data'] = {'goal_title': goal_name}
            response['response_text'] = f"I'll create goal **'{goal_name.title()}'**. Should I go ahead?"
            return response
        elif awaiting_type == 'task_name':
            task_name = message.strip()
            st.session_state.awaiting_info = False
            st.session_state.awaiting_info_type = None
            response['action'] = 'create_task'
            response['needs_confirmation'] = True
            response['pending_data'] = {'task_title': task_name}
            response['response_text'] = f"I'll create task **'{task_name.title()}'** for today. Should I go ahead?"
            return response

    # SHOW actions - display data
    if details['action'] == 'show':
        if details['date'] == 'today' or 'today' in message.lower():
            response['action'] = 'show'
            response['view'] = 'today'
            response['response_text'] = "Here's what's on your schedule for today:"
        elif details['type'] == 'goal':
            response['action'] = 'show'
            response['view'] = 'goals'
            response['response_text'] = "Here are your current goals:"
        elif details['type'] == 'task':
            response['action'] = 'show'
            response['view'] = 'tasks'
            response['response_text'] = "Here are your tasks:"
        elif details['date'] == 'week' or 'upcoming' in message.lower():
            response['action'] = 'show'
            response['view'] = 'upcoming'
            response['response_text'] = "Here's what's coming up:"
        else:
            response['action'] = 'show'
            response['view'] = 'today'
            response['response_text'] = "Here's your schedule:"
        return response

    # CHECK/SUMMARIZE actions
    if details['action'] == 'check':
        if details['type'] == 'email':
            response['action'] = 'check_email'
            response['response_text'] = "Let me check your emails and summarize what's important..."
        else:
            response['action'] = 'daily_summary'
            response['response_text'] = "Here's your daily summary:"
        return response

    # CREATE actions - need confirmation
    if details['action'] == 'create':
        if details['type'] == 'goal' and details['title']:
            # Goal with sessions
            if details['days'] and details['start_time']:
                response['action'] = 'create_goal_with_sessions'
                response['needs_confirmation'] = True
                response['pending_data'] = {
                    'goal_title': details['title'],
                    'days': details['days'],
                    'start_time': details['start_time'],
                    'end_time': details['end_time'] or details['start_time'],
                }
                days_str = format_days_list(details['days'])
                time_str = f"{format_time(details['start_time'])} to {format_time(details['end_time'])}"
                response['response_text'] = f"I'll create goal **'{details['title'].title()}'** with sessions on **{days_str}** from **{time_str}**. Should I go ahead?"
            else:
                # Just a goal without sessions
                response['action'] = 'create_goal'
                response['needs_confirmation'] = True
                response['pending_data'] = {'goal_title': details['title']}
                response['response_text'] = f"I'll create goal **'{details['title'].title()}'**. Should I go ahead?"
            return response

        elif details['type'] == 'task' and details['title']:
            response['action'] = 'create_task'
            response['needs_confirmation'] = True
            response['pending_data'] = {'task_title': details['title']}
            response['response_text'] = f"I'll create task **'{details['title'].title()}'** for today. Should I go ahead?"
            return response

        elif details['type'] == 'session':
            response['action'] = 'create_session'
            response['needs_confirmation'] = True
            response['pending_data'] = details
            response['response_text'] = f"I'll create a session. Should I go ahead?"
            return response

        # Couldn't parse enough details - start guided flow
        if details['type'] == 'goal':
            st.session_state.goal_creation_stage = 'ask_calendar'
            st.session_state.pending_goal = {}
            response['response_text'] = "Great! Would you like to block out time in your calendar for this goal?"
            response['action'] = 'goal_flow_start'
            return response
        elif details['type'] == 'task':
            response['response_text'] = "What would you like to call this task?"
            response['action'] = 'need_task_name'
            return response
        elif details['type']:
            response['response_text'] = f"I'd like to create a {details['type']} for you. What would you like to call it?"
            response['action'] = 'need_more_info'
            return response
        else:
            response['response_text'] = "What would you like me to create? (goal, task, session, meeting)"
            response['action'] = 'need_more_info'
            return response

    # COMPLETE action
    if details['action'] == 'complete':
        response['action'] = 'mark_complete'
        response['response_text'] = "Which item would you like to mark as complete?"
        return response

    # Default help response
    response['response_text'] = """I can help you with:
• **Show items**: "what's on today?", "show my goals", "upcoming tasks"
• **Create items**: "create a goal for MOOC study, weekdays 7:30-9am"
• **Check emails**: "check my emails", "summarize emails"
• **Daily tasks**: "what are my daily tasks?"

What would you like to do?"""
    return response
