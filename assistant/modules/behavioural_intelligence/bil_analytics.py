"""
BIL Analytics
=============
Session tracking, adherence reporting, and weekly reviews.
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
from sqlalchemy import text
import random

from .bil_config import engine
from .bil_models import SessionLog
from .bil_prompts import MISSED_SESSION_PROMPTS

router = APIRouter()


@router.post("/session")
def log_session(session: SessionLog):
    """Log a completed (or missed) session"""
    # Store in behaviour_metrics
    with engine.begin() as conn:
        conn.execute(
            text(
                """
            INSERT INTO behaviour_metrics (date, domain, question, response, sentiment)
            VALUES (:date, :goal, :question, :response, :sentiment)
        """
            ),
            {
                "date": datetime.now(),
                "goal": session.goal_name,
                "question": f"Did you complete {session.goal_name}?",
                "response": "Yes" if session.completed else "No",
                "sentiment": 1.0 if session.completed else 0.0,
            },
        )

        # Update goal completion count if completed
        if session.completed:
            conn.execute(
                text(
                    """
                UPDATE goals
                SET completed = completed + 1, last_update = :now
                WHERE name = :name
            """
                ),
                {"name": session.goal_name, "now": datetime.now()},
            )

    return {
        "status": "logged",
        "message": f"{'✅ Session completed' if session.completed else '⏭️ Session skipped'}: {session.goal_name}",
    }


@router.get("/adherence")
def get_adherence_report():
    """Get weekly adherence report for all goals"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM goals"))
        goals = result.fetchall()

    report = []
    for goal in goals:
        goal_id, name, target, completed, last_update = goal[:5]
        adherence_pct = (completed / max(1, target)) * 100
        status = "✅ On track" if completed >= target else "⚠️ Behind schedule"

        report.append(
            {
                "goal": name,
                "target": target,
                "completed": completed,
                "adherence_pct": round(adherence_pct, 1),
                "status": status,
                "remaining": max(0, target - completed),
            }
        )

    return {"week_of": datetime.now().strftime("%Y-%m-%d"), "adherence": report}


@router.get("/missed-sessions")
def get_missed_sessions():
    """Detect goals that are behind schedule"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM goals"))
        goals = result.fetchall()

    missed = []
    current_day = datetime.now().weekday()  # 0=Monday, 6=Sunday

    for goal in goals:
        goal_id, name, target, completed, last_update = goal[:5]

        # If it's Thursday (3) or later and we're less than 50% complete
        if current_day >= 3 and completed < (target * 0.5):
            remaining = target - completed
            prompt = random.choice(MISSED_SESSION_PROMPTS).format(goal=name)

            missed.append(
                {
                    "goal": name,
                    "target": target,
                    "completed": completed,
                    "remaining": remaining,
                    "suggestion": prompt,
                    "urgency": "HIGH" if current_day >= 5 else "MEDIUM",
                }
            )

    return {"missed_sessions": missed, "count": len(missed)}


@router.get("/weekly-review")
def generate_weekly_review():
    """Generate comprehensive weekly review with insights"""
    with engine.connect() as conn:
        # Get all goals
        goals_result = conn.execute(text("SELECT * FROM goals"))
        goals = goals_result.fetchall()

        # Get this week's behavior metrics
        week_ago = datetime.now() - timedelta(days=7)
        metrics_result = conn.execute(
            text(
                """
            SELECT domain, COUNT(*) as sessions, AVG(sentiment) as avg_sentiment
            FROM behaviour_metrics
            WHERE date >= :week_ago
            GROUP BY domain
        """
            ),
            {"week_ago": week_ago},
        )
        metrics = metrics_result.fetchall()

    # Build review
    review = {
        "week_of": datetime.now().strftime("%Y-%m-%d"),
        "summary": {"total_goals": len(goals), "goals_on_track": 0, "goals_behind": 0},
        "goals_detail": [],
        "hypotheses": [],
    }

    # Analyze each goal
    for goal in goals:
        goal_id, name, target, completed, last_update = goal[:5]
        adherence_pct = (completed / max(1, target)) * 100
        on_track = completed >= target

        if on_track:
            review["summary"]["goals_on_track"] += 1
        else:
            review["summary"]["goals_behind"] += 1

        review["goals_detail"].append(
            {
                "goal": name,
                "target": target,
                "completed": completed,
                "adherence_pct": round(adherence_pct, 1),
                "status": "✅ Achieved" if on_track else "⚠️ Needs attention",
            }
        )

    # Generate 2-3 hypotheses based on data
    hypotheses = []

    # Hypothesis 1: Overall performance
    overall_adherence = (review["summary"]["goals_on_track"] / max(1, len(goals))) * 100
    if overall_adherence >= 75:
        hypotheses.append(
            "🎯 Strong week overall - you're building solid habits. Consider adding a new goal?"
        )
    elif overall_adherence >= 50:
        hypotheses.append(
            "📊 Mixed results this week. What's blocking you from full consistency?"
        )
    else:
        hypotheses.append(
            "🔍 This was a challenging week. Would breaking goals into smaller steps help?"
        )

    # Hypothesis 2: Specific goal insights
    if review["summary"]["goals_behind"] > 0:
        behind_goals = [
            g["goal"] for g in review["goals_detail"] if g["status"] == "⚠️ Needs attention"
        ]
        hypotheses.append(
            f"💡 You struggled with {', '.join(behind_goals[:2])}. "
            "Are these still aligned with your priorities?"
        )

    # Hypothesis 3: Encouragement or adjustment
    if review["summary"]["goals_on_track"] > 0:
        on_track_goals = [
            g["goal"] for g in review["goals_detail"] if g["status"] == "✅ Achieved"
        ]
        hypotheses.append(
            f"🌟 Your consistency with {', '.join(on_track_goals[:2])} is excellent! "
            "That's the momentum we want."
        )

    review["hypotheses"] = hypotheses[:3]  # Limit to 3

    return review
