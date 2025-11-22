"""
Action Execution
================
Execute confirmed actions (create goals, tasks, calendar events, email operations).
"""

from datetime import date, timedelta
from parsers import DAY_NAMES, parse_end_date

# Import action functions from split modules (direct imports for Streamlit compatibility)
from calendar_actions import (
    create_calendar_event,
    list_calendar_events,
    get_calendar_status,
    check_calendar_conflicts,
    hide_calendar_event,
    delete_calendar_event_action,
)
from email_actions import (
    get_gmail_client,
    search_emails,
    fetch_new_emails,
    archive_email,
    delete_email,
    mark_email_read,
    mark_email_unread,
    star_email,
    detect_email_events,
    list_pending_events,
    approve_event,
    reject_event,
)
from summary_actions import (
    get_daily_summary,
    check_and_summarize_emails,
    get_all_daily_tasks,
)


def execute_pending_action(client, pending_data: dict, action_type: str) -> str:
    """Execute a confirmed action and return result message."""
    try:
        if action_type == 'create_goal_with_sessions':
            # Get title from either format (guided flow or direct)
            goal_title = pending_data.get('title') or pending_data.get('goal_title', 'Untitled')
            goal_title = goal_title.title()
            category = pending_data.get('category')
            end_date_str = pending_data.get('end_date', '6 months')

            # Parse end date
            end_date = parse_end_date(end_date_str)

            # Create the goal
            goal_item = {
                'type': 'goal',
                'title': goal_title,
                'date': str(date.today()),
                'status': 'upcoming',
                'source': 'manual',
            }
            if category:
                goal_item['category'] = category

            created_goal = client.create_item(goal_item)
            goal_id = created_goal['id']

            # Generate all session dates until end_date
            sessions_created = 0
            calendar_added = 0
            days = pending_data['days']

            # Start from today and iterate through weeks until end_date
            current_date = date.today()
            while current_date <= end_date:
                # Check if this day of week is in our target days
                if current_date.weekday() in days:
                    session_title = f"{goal_title} - {DAY_NAMES[current_date.weekday()]}"

                    # Create session in DB
                    session_item = {
                        'type': 'session',
                        'title': session_title,
                        'date': str(current_date),
                        'start_time': pending_data['start_time'],
                        'end_time': pending_data['end_time'],
                        'status': 'upcoming',
                        'source': 'manual',
                        'goal_id': goal_id,
                    }
                    if category:
                        session_item['category'] = category
                    client.create_item(session_item)
                    sessions_created += 1

                    # Add to Google Calendar
                    if create_calendar_event(session_title, current_date, pending_data['start_time'], pending_data['end_time']):
                        calendar_added += 1

                current_date += timedelta(days=1)

            # Build result message
            result = f"✅ Created goal **'{goal_title}'**"
            if category:
                result += f" ({category})"
            result += f" with {sessions_created} sessions until {end_date.strftime('%B %d, %Y')}!"
            if calendar_added > 0:
                result += f"\n📅 Added {calendar_added} events to Google Calendar!"
            elif sessions_created > 0:
                result += "\n⚠️ Couldn't add to calendar (check if orchestrator is running at :8000)"

            return result

        elif action_type == 'create_goal':
            goal_title = pending_data.get('title') or pending_data.get('goal_title', 'Untitled')
            goal_title = goal_title.title()
            category = pending_data.get('category')

            goal_item = {
                'type': 'goal',
                'title': goal_title,
                'date': str(date.today()),
                'status': 'upcoming',
                'source': 'manual',
            }
            if category:
                goal_item['category'] = category

            client.create_item(goal_item)
            result = f"✅ Created goal **'{goal_title}'**"
            if category:
                result += f" ({category})"
            return result + "!"

        elif action_type == 'create_task':
            task_item = {
                'type': 'task',
                'title': pending_data['task_title'].title(),
                'date': str(date.today()),
                'status': 'upcoming',
                'source': 'manual',
            }
            client.create_item(task_item)
            return f"✅ Created task **'{pending_data['task_title'].title()}'**!"

        elif action_type == 'create_task_with_calendar':
            task_title = pending_data['task_title'].title()
            task_date_str = pending_data.get('date', 'today')
            start_time = pending_data['start_time']
            end_time = pending_data['end_time']

            # Resolve date
            if task_date_str == 'today':
                task_date = date.today()
            elif task_date_str == 'tomorrow':
                task_date = date.today() + timedelta(days=1)
            else:
                task_date = date.fromisoformat(task_date_str)

            # Create task in DB
            task_item = {
                'type': 'task',
                'title': task_title,
                'date': str(task_date),
                'start_time': start_time,
                'end_time': end_time,
                'status': 'upcoming',
                'source': 'manual',
            }
            client.create_item(task_item)

            # Add to Google Calendar
            calendar_added = create_calendar_event(task_title, task_date, start_time, end_time)

            result = f"✅ Created task **'{task_title}'** for {task_date.strftime('%A, %b %d')}!"
            if calendar_added:
                result += f"\n📅 Added to Google Calendar ({start_time} - {end_time})!"
            else:
                result += "\n⚠️ Couldn't add to calendar (check if orchestrator is running at :8000)"

            return result

        # EMAIL ACTIONS (with confirmation)
        elif action_type == 'archive_email':
            return archive_email(pending_data)

        elif action_type == 'delete_email':
            return delete_email(pending_data)

        # CALENDAR ACTIONS (with confirmation)
        elif action_type == 'hide_calendar_event':
            return hide_calendar_event(pending_data)

        elif action_type == 'delete_calendar_event':
            return delete_calendar_event_action(pending_data)

        return "✅ Done!"
    except Exception as e:
        return f"❌ Error: {str(e)}"
