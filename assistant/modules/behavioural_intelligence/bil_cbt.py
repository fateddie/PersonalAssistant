"""
CBT Thought Log Module (Phase 3.5 Week 4)
=========================================
Cognitive Behavioral Therapy thought challenging and reframing.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text

# Database connection
DB_PATH = "assistant/data/memory.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

# Common cognitive distortions
COGNITIVE_DISTORTIONS = {
    "all_or_nothing": {
        "name": "All-or-Nothing Thinking",
        "description": "Seeing things in black and white categories",
        "example": "If I don't do this perfectly, I'm a total failure",
    },
    "catastrophizing": {
        "name": "Catastrophizing",
        "description": "Expecting the worst possible outcome",
        "example": "This mistake will ruin everything",
    },
    "mind_reading": {
        "name": "Mind Reading",
        "description": "Assuming you know what others are thinking",
        "example": "They think I'm incompetent",
    },
    "fortune_telling": {
        "name": "Fortune Telling",
        "description": "Predicting negative outcomes without evidence",
        "example": "This project will definitely fail",
    },
    "should_statements": {
        "name": "Should Statements",
        "description": "Rigid rules about how things should be",
        "example": "I should be able to handle everything",
    },
    "emotional_reasoning": {
        "name": "Emotional Reasoning",
        "description": "Believing something is true because it feels true",
        "example": "I feel anxious, so something must be wrong",
    },
    "labeling": {
        "name": "Labeling",
        "description": "Attaching a negative label to yourself or others",
        "example": "I'm such an idiot",
    },
    "overgeneralization": {
        "name": "Overgeneralization",
        "description": "Drawing broad conclusions from single events",
        "example": "I always mess things up",
    },
    "personalization": {
        "name": "Personalization",
        "description": "Blaming yourself for things outside your control",
        "example": "The project failed because of me",
    },
    "filtering": {
        "name": "Mental Filtering",
        "description": "Focusing only on the negative aspects",
        "example": "Despite 9 good reviews, I only think about the 1 criticism",
    },
}


def create_thought_log(
    situation: str,
    automatic_thought: str,
    cognitive_distortion: Optional[str] = None,
    evidence_for: Optional[str] = None,
    evidence_against: Optional[str] = None,
    reframe: Optional[str] = None,
    item_id: Optional[str] = None,
) -> int:
    """
    Create a CBT thought log entry.

    Args:
        situation: What triggered the thought
        automatic_thought: The automatic negative thought
        cognitive_distortion: Type of distortion (optional)
        evidence_for: Evidence supporting the thought
        evidence_against: Evidence against the thought
        reframe: A more balanced thought
        item_id: Optional related task/goal ID

    Returns:
        The log ID
    """
    now = datetime.now()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO thought_logs
                (situation, automatic_thought, cognitive_distortion,
                 evidence_for, evidence_against, reframe, item_id, created_at, source)
                VALUES (:situation, :thought, :distortion, :evidence_for,
                        :evidence_against, :reframe, :item_id, :now, 'cbt')
            """
            ),
            {
                "situation": situation,
                "thought": automatic_thought,
                "distortion": cognitive_distortion,
                "evidence_for": evidence_for,
                "evidence_against": evidence_against,
                "reframe": reframe,
                "item_id": item_id,
                "now": now.isoformat(),
            },
        )

        row = conn.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]


def update_thought_log(
    log_id: int,
    evidence_for: Optional[str] = None,
    evidence_against: Optional[str] = None,
    reframe: Optional[str] = None,
    cognitive_distortion: Optional[str] = None,
    outcome: Optional[str] = None,
) -> bool:
    """
    Update an existing thought log (add evidence, reframe, outcome).

    Args:
        log_id: The log ID
        evidence_for: Evidence supporting the thought
        evidence_against: Evidence against the thought
        reframe: A more balanced thought
        cognitive_distortion: Type of distortion
        outcome: How you felt after reframing

    Returns:
        True if successful
    """
    updates = []
    params = {"id": log_id}

    if evidence_for is not None:
        updates.append("evidence_for = :evidence_for")
        params["evidence_for"] = evidence_for
    if evidence_against is not None:
        updates.append("evidence_against = :evidence_against")
        params["evidence_against"] = evidence_against
    if reframe is not None:
        updates.append("reframe = :reframe")
        params["reframe"] = reframe
    if cognitive_distortion is not None:
        updates.append("cognitive_distortion = :distortion")
        params["distortion"] = cognitive_distortion
    if outcome is not None:
        updates.append("outcome = :outcome")
        params["outcome"] = outcome

    if not updates:
        return False

    query = f"UPDATE thought_logs SET {', '.join(updates)} WHERE id = :id"

    with engine.begin() as conn:
        result = conn.execute(text(query), params)
        return result.rowcount > 0


def get_thought_logs(
    days: int = 7,
    include_incomplete: bool = True,
) -> List[Dict[str, Any]]:
    """
    Get recent thought logs.

    Args:
        days: Number of days to look back
        include_incomplete: Include logs without reframes

    Returns:
        List of thought log dictionaries
    """
    start_date = (datetime.now() - timedelta(days=days)).isoformat()

    query = """
        SELECT id, situation, automatic_thought, cognitive_distortion,
               evidence_for, evidence_against, reframe, outcome,
               item_id, created_at
        FROM thought_logs
        WHERE source = 'cbt' AND created_at >= :start
    """

    if not include_incomplete:
        query += " AND reframe IS NOT NULL"

    query += " ORDER BY created_at DESC"

    with engine.connect() as conn:
        rows = conn.execute(text(query), {"start": start_date}).fetchall()

    return [
        {
            "id": row[0],
            "situation": row[1],
            "automatic_thought": row[2],
            "cognitive_distortion": row[3],
            "evidence_for": row[4],
            "evidence_against": row[5],
            "reframe": row[6],
            "outcome": row[7],
            "item_id": row[8],
            "created_at": row[9],
            "is_complete": row[6] is not None,
        }
        for row in rows
    ]


def get_distortion_list() -> List[Dict[str, str]]:
    """
    Get list of cognitive distortions for UI.
    """
    return [{"key": key, **value} for key, value in COGNITIVE_DISTORTIONS.items()]


def get_distortion_stats(days: int = 30) -> Dict[str, int]:
    """
    Get counts of each cognitive distortion type.

    Args:
        days: Number of days to analyze

    Returns:
        Dictionary of distortion type -> count
    """
    start_date = (datetime.now() - timedelta(days=days)).isoformat()

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT cognitive_distortion, COUNT(*) as cnt
                FROM thought_logs
                WHERE source = 'cbt'
                AND cognitive_distortion IS NOT NULL
                AND created_at >= :start
                GROUP BY cognitive_distortion
                ORDER BY cnt DESC
            """
            ),
            {"start": start_date},
        ).fetchall()

    return {row[0]: row[1] for row in rows}


def suggest_reframe(automatic_thought: str, distortion: Optional[str] = None) -> str:
    """
    Suggest a reframe based on the thought and distortion type.

    Args:
        automatic_thought: The original thought
        distortion: Type of cognitive distortion

    Returns:
        Suggested reframe prompt
    """
    prompts = {
        "all_or_nothing": "What would a more balanced view look like? Is there a middle ground?",
        "catastrophizing": "What's the most likely outcome? What would you tell a friend?",
        "mind_reading": "What evidence do you actually have? Could there be other explanations?",
        "fortune_telling": "Has this prediction come true before? What are other possible outcomes?",
        "should_statements": "What if you replaced 'should' with 'could' or 'would like to'?",
        "emotional_reasoning": "Just because you feel it, does that make it true?",
        "labeling": "Would you use this label for a friend in the same situation?",
        "overgeneralization": "Is this really 'always' or 'never'? What are the exceptions?",
        "personalization": "What factors outside your control contributed to this?",
        "filtering": "What positive aspects might you be overlooking?",
    }

    if distortion and distortion in prompts:
        return prompts[distortion]

    return "What would you tell a friend in this situation? What evidence contradicts this thought?"


def get_quick_challenges() -> List[Dict[str, str]]:
    """
    Get quick thought-challenging questions.
    """
    return [
        {"question": "Is this thought based on facts or feelings?"},
        {"question": "What would I tell a friend who had this thought?"},
        {"question": "Will this matter in 5 years?"},
        {"question": "Am I jumping to conclusions?"},
        {"question": "What's the worst that could actually happen?"},
        {"question": "What's the best that could happen?"},
        {"question": "What's the most realistic outcome?"},
        {"question": "Is there another way to look at this?"},
    ]
