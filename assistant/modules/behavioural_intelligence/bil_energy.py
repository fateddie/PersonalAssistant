"""
Energy Tracking Module (Phase 3.5 Week 4)
=========================================
Track energy levels throughout the day to optimize productivity.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text

# Database connection
DB_PATH = "assistant/data/memory.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def record_energy(level: int, time_of_day: str = "current") -> bool:
    """
    Record energy level.

    Args:
        level: Energy level 1-5 (1=exhausted, 5=energized)
        time_of_day: "am", "pm", or "current" (auto-detect)

    Returns:
        True if successful
    """
    if level < 1 or level > 5:
        return False

    today = date.today().isoformat()
    now = datetime.now()

    # Auto-detect time of day
    if time_of_day == "current":
        time_of_day = "am" if now.hour < 12 else "pm"

    column = "energy_am" if time_of_day == "am" else "energy_pm"

    with engine.begin() as conn:
        # Check if record exists
        row = conn.execute(
            text("SELECT id FROM daily_reflections WHERE date = :date"),
            {"date": today},
        ).fetchone()

        if row:
            conn.execute(
                text(f"UPDATE daily_reflections SET {column} = :level WHERE date = :date"),
                {"level": level, "date": today},
            )
        else:
            conn.execute(
                text(
                    f"""
                    INSERT INTO daily_reflections (date, {column})
                    VALUES (:date, :level)
                """
                ),
                {"date": today, "level": level},
            )

    return True


def get_todays_energy() -> Dict[str, Any]:
    """
    Get today's energy levels.
    """
    today = date.today().isoformat()

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT energy_am, energy_pm FROM daily_reflections WHERE date = :date"),
            {"date": today},
        ).fetchone()

    if not row:
        return {"am": None, "pm": None}

    return {"am": row[0], "pm": row[1]}


def get_energy_history(days: int = 14) -> List[Dict[str, Any]]:
    """
    Get energy level history.

    Args:
        days: Number of days to look back

    Returns:
        List of daily energy records
    """
    start_date = (date.today() - timedelta(days=days)).isoformat()

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT date, energy_am, energy_pm
                FROM daily_reflections
                WHERE date >= :start
                AND (energy_am IS NOT NULL OR energy_pm IS NOT NULL)
                ORDER BY date DESC
            """
            ),
            {"start": start_date},
        ).fetchall()

    return [
        {
            "date": row[0],
            "am": row[1],
            "pm": row[2],
            "avg": (
                ((row[1] or 0) + (row[2] or 0)) / (bool(row[1]) + bool(row[2]))
                if (row[1] or row[2])
                else None
            ),
        }
        for row in rows
    ]


def get_energy_patterns() -> Dict[str, Any]:
    """
    Analyze energy patterns over time.

    Returns:
        Pattern analysis
    """
    # Last 30 days
    start_date = (date.today() - timedelta(days=30)).isoformat()

    with engine.connect() as conn:
        # Average AM energy
        row = conn.execute(
            text(
                """
                SELECT AVG(energy_am), AVG(energy_pm)
                FROM daily_reflections
                WHERE date >= :start
                AND (energy_am IS NOT NULL OR energy_pm IS NOT NULL)
            """
            ),
            {"start": start_date},
        ).fetchone()

        avg_am = round(row[0], 1) if row[0] else None
        avg_pm = round(row[1], 1) if row[1] else None

        # Best days of week (by average energy)
        rows = conn.execute(
            text(
                """
                SELECT
                    CASE CAST(strftime('%w', date) AS INTEGER)
                        WHEN 0 THEN 'Sunday'
                        WHEN 1 THEN 'Monday'
                        WHEN 2 THEN 'Tuesday'
                        WHEN 3 THEN 'Wednesday'
                        WHEN 4 THEN 'Thursday'
                        WHEN 5 THEN 'Friday'
                        WHEN 6 THEN 'Saturday'
                    END as day_name,
                    AVG((COALESCE(energy_am, 0) + COALESCE(energy_pm, 0)) /
                        (CASE WHEN energy_am IS NOT NULL THEN 1 ELSE 0 END +
                         CASE WHEN energy_pm IS NOT NULL THEN 1 ELSE 0 END)) as avg_energy
                FROM daily_reflections
                WHERE date >= :start
                AND (energy_am IS NOT NULL OR energy_pm IS NOT NULL)
                GROUP BY strftime('%w', date)
                ORDER BY avg_energy DESC
            """
            ),
            {"start": start_date},
        ).fetchall()

        day_patterns = [{"day": r[0], "avg_energy": round(r[1], 1)} for r in rows if r[1]]

    return {
        "avg_am": avg_am,
        "avg_pm": avg_pm,
        "trend": "higher_am" if (avg_am or 0) > (avg_pm or 0) else "higher_pm",
        "day_patterns": day_patterns,
        "best_day": day_patterns[0]["day"] if day_patterns else None,
        "lowest_day": day_patterns[-1]["day"] if day_patterns else None,
    }


def get_energy_recommendations() -> List[str]:
    """
    Get personalized energy recommendations based on patterns.
    """
    patterns = get_energy_patterns()
    recommendations = []

    if patterns["avg_am"] and patterns["avg_pm"]:
        if patterns["avg_am"] > patterns["avg_pm"]:
            recommendations.append(
                "Your energy peaks in the morning. Schedule demanding tasks before noon."
            )
        else:
            recommendations.append(
                "Your energy is higher in the afternoon. Save complex tasks for after lunch."
            )

        if patterns["avg_am"] and patterns["avg_am"] < 3:
            recommendations.append(
                "Morning energy is low. Consider reviewing your sleep habits or morning routine."
            )

        if patterns["avg_pm"] and patterns["avg_pm"] < 3:
            recommendations.append(
                "Afternoon energy drops. Try a short walk or energizing break after lunch."
            )

    if patterns["best_day"]:
        recommendations.append(
            f"{patterns['best_day']} tends to be your highest-energy day. Plan important work then."
        )

    if patterns["lowest_day"]:
        recommendations.append(
            f"Energy tends to be lower on {patterns['lowest_day']}. Schedule lighter tasks."
        )

    if not recommendations:
        recommendations.append("Start tracking your energy to get personalized recommendations.")

    return recommendations


ENERGY_LABELS = {
    1: "Exhausted",
    2: "Low",
    3: "Moderate",
    4: "Good",
    5: "Energized",
}


def get_energy_label(level: int) -> str:
    """Get human-readable label for energy level."""
    return ENERGY_LABELS.get(level, "Unknown")
