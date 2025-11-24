"""
BIL Event Handlers
==================
Morning check-in, evening reflection, and Phase 3.5 discipline handlers.
"""

import os
import random
from datetime import datetime, timedelta
from sqlalchemy import text

from .bil_config import (
    engine,
    SUPABASE_AVAILABLE,
    PROGRESS_REPORTS_AVAILABLE,
    _get_supabase_client,
    get_tasks_for_project,
    get_managementteam_activity,
    get_asksharon_activity,
)
from .bil_prompts import (
    MORNING_PROMPTS,
    EVENING_PROMPTS,
    MISSED_SESSION_PROMPTS,
    ENCOURAGEMENT_PROMPTS,
)
from .bil_rituals import (
    check_needs_evening_planning,
    check_needs_morning_fallback,
    get_morning_display_data,
)
from .bil_streaks import get_at_risk_streaks


def handle_morning_checkin(data):
    """
    Morning check-in handler

    Displays:
    - Morning greeting
    - Active ManagementTeam projects (from shared memory)
    - Related AskSharon tasks
    """
    prompt = random.choice(MORNING_PROMPTS)
    print(f"\n{prompt}")
    print(f"Time: {data.get('time')}\n")

    # Show ManagementTeam projects (Option 1 from user request)
    if SUPABASE_AVAILABLE:
        try:
            supabase = _get_supabase_client()

            # Query active business projects
            result = (
                supabase.table("project_decisions")
                .select("project_name, decision, agent_name, created_at, notes")
                .in_("decision", ["approved", "in_progress"])
                .order("created_at", desc=True)
                .limit(5)
                .execute()
            )

            if result.data and len(result.data) > 0:
                print("📊 Active Business Projects (ManagementTeam):")
                print("=" * 50)

                for project in result.data:
                    project_name = project["project_name"]
                    decision = project["decision"]
                    agent = project["agent_name"]

                    # Get task count for this project
                    tasks = get_tasks_for_project(project_name, include_completed=False)
                    task_count = len(tasks) if tasks else 0
                    completed_tasks = get_tasks_for_project(project_name, include_completed=True)
                    completed_count = (
                        len([t for t in completed_tasks if t.get("completed", False)])
                        if completed_tasks
                        else 0
                    )

                    # Display project with task count
                    status_emoji = "🟢" if decision == "approved" else "🟡"
                    print(f"\n  {status_emoji} {project_name}")
                    print(f"     Status: {decision.upper()} (by {agent})")

                    if task_count > 0:
                        print(f"     Tasks: {completed_count} completed, {task_count} pending")
                        print(
                            f"     💡 View tasks: python assistant/core/supabase_memory.py project --project '{project_name}'"
                        )
                    else:
                        print(f"     ⚠️  No tasks created yet")
                        print(
                            f"     💡 Create tasks: python assistant/core/supabase_memory.py add-task --project '{project_name}'"
                        )

                print("\n" + "=" * 50)
                print(f"📈 Total: {len(result.data)} active business projects\n")
            else:
                print("ℹ️  No active business projects found in ManagementTeam\n")

        except Exception as e:
            print(f"⚠️  Could not load ManagementTeam projects: {e}\n")
    else:
        print("ℹ️  ManagementTeam integration not configured\n")

    # Optional: Show yesterday's summary
    if (
        PROGRESS_REPORTS_AVAILABLE
        and os.getenv("MORNING_SHOW_YESTERDAY", "false").lower() == "true"
    ):
        try:
            print("\n📅 Yesterday's Activity Summary")
            print("=" * 50)

            yesterday = datetime.now() - timedelta(days=1)
            mt_activity = get_managementteam_activity(yesterday)
            as_activity = get_asksharon_activity(yesterday)

            total_activity = (
                mt_activity["total_projects"]
                + as_activity["total_created"]
                + as_activity["total_completed"]
            )

            if total_activity > 0:
                print(f"  Business projects: {mt_activity['total_projects']} worked on")
                print(
                    f"  Tasks: {as_activity['total_created']} created, {as_activity['total_completed']} completed"
                )
                print(f"\n  💡 Full report: python scripts/progress_report.py yesterday")
            else:
                print("  No activity recorded yesterday")

            print("=" * 50)
            print("")

        except Exception as e:
            print(f"⚠️  Could not load yesterday's summary: {e}\n")


def handle_evening_reflection(data):
    """Evening reflection handler"""
    prompt = random.choice(EVENING_PROMPTS)
    print(f"\n{prompt}")

    # Check for missed sessions
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM goals"))
        goals = result.fetchall()

    for goal in goals:
        goal_id, name, target, completed, last_update = goal[:5]
        adherence = completed / max(1, target)

        if adherence >= 0.75:
            encouragement = random.choice(ENCOURAGEMENT_PROMPTS).format(
                percent=int(adherence * 100), sessions=completed, goal=name
            )
            print(f"  {encouragement}")
        elif adherence < 0.5:
            suggestion = random.choice(MISSED_SESSION_PROMPTS).format(goal=name)
            print(f"  🔔 {suggestion}")

    print("")


def handle_evening_planning(data):
    """
    Phase 3.5: Evening planning handler (6pm trigger).

    Prompts user to plan tomorrow if not already done.
    """
    result = check_needs_evening_planning()

    print(f"\n🌙 Evening Planning Check ({data.get('time', '18:00')})")
    print("=" * 50)

    if result["needs_planning"]:
        print(f"\n📋 {result['message']}")
        print(f"   Plan for: {result['target_date'].strftime('%A, %B %d')}")
        print("\n   Open the Discipline tab in AskSharon to:")
        print("   1. Reflect on what went well today")
        print("   2. Set your Top 3 priorities for tomorrow")
        print("   3. Define one thing to make tomorrow great")

        # Check at-risk streaks
        at_risk = get_at_risk_streaks()
        if at_risk:
            print("\n   ⚠️ Streaks at risk:")
            for s in at_risk:
                print(f"      - {s['activity']}: {s['current_streak']} days")
    else:
        print(f"\n{result['message']}")

    print("=" * 50 + "\n")


def handle_morning_fallback(data):
    """
    Phase 3.5: Morning fallback handler (8am trigger).

    Shows today's plan or prompts for quick planning if evening was missed.
    """
    result = check_needs_morning_fallback()

    print(f"\n☀️ Morning Plan Check ({data.get('time', '08:00')})")
    print("=" * 50)

    if result["needs_fallback"]:
        print(f"\n⚡ {result['message']}")
        print("   No evening plan was found for today.")
        print("\n   Quick actions:")
        print("   1. Open the Discipline tab for quick planning")
        print("   2. Set just your Top 3 priorities")
        print("   3. Start your day with clarity!")
    else:
        print(f"\n{result['message']}")
        morning_data = get_morning_display_data()
        if morning_data["has_plan"]:
            if morning_data["is_fallback"]:
                print("   (Created via morning fallback)")
            print(f"\n   🎯 One thing to make today great:")
            print(f"      {morning_data['one_thing_great']}")

    print("=" * 50 + "\n")
