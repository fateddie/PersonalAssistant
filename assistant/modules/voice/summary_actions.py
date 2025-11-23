"""
Summary Actions
===============
Daily summary and overview functions.
"""

import requests
from datetime import date, timedelta, datetime
from typing import Dict


def get_daily_summary(client) -> str:
    """Generate a daily summary of tasks and items."""
    today = date.today()
    try:
        result = client.list_items(date_from=today, date_to=today, limit=50)
        items = result["items"]

        if not items:
            return "You have nothing scheduled for today. Enjoy your free time! 🎉"

        summary_parts = [f"📅 **Today ({today.strftime('%A, %B %d')})**\n"]

        by_type: Dict = {}
        for item in items:
            item_type = item["type"]
            if item_type not in by_type:
                by_type[item_type] = []
            by_type[item_type].append(item)

        type_emoji = {
            "goal": "🎯",
            "task": "✅",
            "session": "⏰",
            "meeting": "👥",
            "webinar": "📺",
            "appointment": "📅",
        }

        for item_type, type_items in by_type.items():
            emoji = type_emoji.get(item_type, "📄")
            summary_parts.append(f"\n**{emoji} {item_type.title()}s ({len(type_items)})**")
            for item in type_items:
                time_str = f" at {item['start_time']}" if item.get("start_time") else ""
                status_mark = "✓" if item["status"] == "done" else "○"
                summary_parts.append(f"  {status_mark} {item['title']}{time_str}")

        return "\n".join(summary_parts)
    except Exception as e:
        return f"Error getting summary: {str(e)}"


def check_and_summarize_emails() -> str:
    """Check emails via orchestrator API and return summary."""
    try:
        response = requests.get(
            "http://localhost:8000/emails/summarise",
            params={"fetch_new": True, "limit": 10, "generate_ai_summary": True},
            timeout=30,
        )

        if response.status_code != 200:
            return (
                "❌ Couldn't check emails. Make sure the orchestrator is running at localhost:8000"
            )

        data = response.json()

        summary_parts = ["📧 **Email Summary**\n"]

        total = data.get("total", 0)
        by_priority = data.get("by_priority", {})
        summary_parts.append(
            f"**{total} emails** - {by_priority.get('HIGH', 0)} high, {by_priority.get('MEDIUM', 0)} medium, {by_priority.get('LOW', 0)} low priority\n"
        )

        if data.get("overview"):
            summary_parts.append(f"**AI Overview:**\n{data['overview']}\n")

        emails = data.get("emails", [])
        high_priority = [e for e in emails if e.get("priority") == "HIGH"]
        if high_priority:
            summary_parts.append("**🔴 High Priority:**")
            for email in high_priority[:5]:
                summary_parts.append(f"  • {email['subject'][:60]}")

        summary_parts.append("\n**📬 Recent:**")
        for email in emails[:5]:
            priority_icon = (
                "🔴"
                if email.get("priority") == "HIGH"
                else "🟡" if email.get("priority") == "MEDIUM" else "🟢"
            )
            summary_parts.append(f"  {priority_icon} {email['subject'][:50]}")

        return "\n".join(summary_parts)

    except requests.exceptions.ConnectionError:
        return "❌ Couldn't connect to email service. Start the orchestrator with: `uvicorn assistant.core.orchestrator:app --port 8000 --reload`"
    except Exception as e:
        return f"❌ Error checking emails: {str(e)}"


def get_all_daily_tasks(client) -> str:
    """Get comprehensive daily task list across all types."""
    today = date.today()
    next_week = today + timedelta(days=7)

    try:
        today_result = client.list_items(date_from=today, date_to=today, limit=50)
        today_items = today_result["items"]

        upcoming_result = client.list_items(
            date_from=today, date_to=next_week, status="upcoming", limit=50
        )
        upcoming_items = [i for i in upcoming_result["items"] if i["date"] != str(today)]

        goals_result = client.list_items(type=["goal"], limit=20)
        goals = goals_result["items"]

        summary_parts = [f"📋 **Your Daily Overview - {today.strftime('%A, %B %d')}**\n"]

        if today_items:
            summary_parts.append("**📅 Today's Schedule:**")
            type_emoji = {
                "goal": "🎯",
                "task": "✅",
                "session": "⏰",
                "meeting": "👥",
                "webinar": "📺",
                "appointment": "📅",
            }
            for item in today_items:
                emoji = type_emoji.get(item["type"], "📄")
                time_str = f" at {item['start_time']}" if item.get("start_time") else ""
                status_mark = "✓" if item["status"] == "done" else "○"
                summary_parts.append(f"  {status_mark} {emoji} {item['title']}{time_str}")
        else:
            summary_parts.append("**📅 Today:** Nothing scheduled")

        active_goals = [g for g in goals if g["status"] != "done"]
        if active_goals:
            summary_parts.append(f"\n**🎯 Active Goals ({len(active_goals)}):**")
            for goal in active_goals[:5]:
                summary_parts.append(f"  • {goal['title']}")

        if upcoming_items:
            summary_parts.append(f"\n**📆 Coming Up ({len(upcoming_items)} items):**")
            for item in upcoming_items[:5]:
                item_date = datetime.fromisoformat(item["date"]).strftime("%a")
                summary_parts.append(f"  • {item_date}: {item['title']}")

        total_today = len(today_items)
        done_today = len([i for i in today_items if i["status"] == "done"])
        if total_today > 0:
            summary_parts.append(f"\n**Progress:** {done_today}/{total_today} completed today")

        return "\n".join(summary_parts)

    except Exception as e:
        return f"Error getting daily tasks: {str(e)}"
