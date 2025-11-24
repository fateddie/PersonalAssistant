"""
Fitness Database Initialization (Phase 4)
=========================================
Creates workout and exercise tracking tables.
"""

from sqlalchemy import create_engine, text
from pathlib import Path

DB_PATH = "assistant/data/memory.db"


def init_fitness_tables():
    """Create all Phase 4 fitness tables if they don't exist."""
    engine = create_engine(f"sqlite:///{DB_PATH}")

    Path("assistant/data").mkdir(parents=True, exist_ok=True)

    with engine.begin() as conn:
        # Exercise library (reference data)
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                muscle_group TEXT,
                equipment TEXT DEFAULT 'bodyweight',
                description TEXT,
                video_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Workout templates
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS workout_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                duration_minutes INTEGER DEFAULT 30,
                difficulty TEXT DEFAULT 'intermediate',
                category TEXT,
                exercises_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Workout sessions (actual performed workouts)
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS workout_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                duration_minutes INTEGER,
                status TEXT DEFAULT 'in_progress',
                overall_rpe INTEGER CHECK(overall_rpe BETWEEN 1 AND 10),
                notes TEXT,
                calories_burned INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES workout_templates(id)
            )
        """
            )
        )

        # Exercise logs (sets/reps for each exercise in a session)
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS exercise_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                set_number INTEGER NOT NULL,
                reps INTEGER,
                weight_kg REAL,
                duration_seconds INTEGER,
                rpe INTEGER CHECK(rpe BETWEEN 1 AND 10),
                notes TEXT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES workout_sessions(id),
                FOREIGN KEY (exercise_id) REFERENCES exercises(id)
            )
        """
            )
        )

        # Personal records
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS personal_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_id INTEGER NOT NULL,
                record_type TEXT NOT NULL,
                value REAL NOT NULL,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id INTEGER,
                FOREIGN KEY (exercise_id) REFERENCES exercises(id),
                FOREIGN KEY (session_id) REFERENCES workout_sessions(id)
            )
        """
            )
        )

        # Seed common bodyweight exercises
        exercises = [
            ("Push-ups", "strength", "chest", "bodyweight", "Standard push-up"),
            ("Squats", "strength", "legs", "bodyweight", "Bodyweight squat"),
            ("Lunges", "strength", "legs", "bodyweight", "Alternating lunges"),
            ("Plank", "core", "abs", "bodyweight", "Standard plank hold"),
            ("Burpees", "cardio", "full_body", "bodyweight", "Full burpee with jump"),
            (
                "Mountain Climbers",
                "cardio",
                "core",
                "bodyweight",
                "Running in plank position",
            ),
            ("Jumping Jacks", "cardio", "full_body", "bodyweight", "Standard jumping jacks"),
            ("Tricep Dips", "strength", "arms", "bodyweight", "Using chair or bench"),
            ("Glute Bridges", "strength", "glutes", "bodyweight", "Hip thrust from floor"),
            ("Superman", "strength", "back", "bodyweight", "Back extension on floor"),
            ("Crunches", "core", "abs", "bodyweight", "Standard crunches"),
            ("Leg Raises", "core", "abs", "bodyweight", "Lying leg raises"),
            ("High Knees", "cardio", "legs", "bodyweight", "Running in place with high knees"),
            ("Wall Sit", "strength", "legs", "bodyweight", "Isometric wall squat hold"),
            ("Side Plank", "core", "obliques", "bodyweight", "Side plank hold"),
        ]

        for name, category, muscle, equipment, desc in exercises:
            conn.execute(
                text(
                    """
                    INSERT OR IGNORE INTO exercises (name, category, muscle_group, equipment, description)
                    VALUES (:name, :category, :muscle, :equipment, :desc)
                """
                ),
                {
                    "name": name,
                    "category": category,
                    "muscle": muscle,
                    "equipment": equipment,
                    "desc": desc,
                },
            )

        # Seed a default 30-min bodyweight workout template
        import json

        default_workout = [
            {"exercise": "Jumping Jacks", "sets": 1, "duration": 60, "rest": 30},
            {"exercise": "Squats", "sets": 3, "reps": 15, "rest": 45},
            {"exercise": "Push-ups", "sets": 3, "reps": 10, "rest": 45},
            {"exercise": "Lunges", "sets": 3, "reps": 12, "rest": 45},
            {"exercise": "Plank", "sets": 3, "duration": 30, "rest": 30},
            {"exercise": "Mountain Climbers", "sets": 3, "duration": 30, "rest": 30},
            {"exercise": "Glute Bridges", "sets": 3, "reps": 15, "rest": 30},
            {"exercise": "Burpees", "sets": 2, "reps": 8, "rest": 60},
            {"exercise": "Crunches", "sets": 3, "reps": 20, "rest": 30},
        ]

        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO workout_templates (name, description, duration_minutes, difficulty, category, exercises_json)
                VALUES (:name, :desc, :duration, :difficulty, :category, :exercises)
            """
            ),
            {
                "name": "30-Min Full Body",
                "desc": "Complete bodyweight workout targeting all major muscle groups",
                "duration": 30,
                "difficulty": "intermediate",
                "category": "full_body",
                "exercises": json.dumps(default_workout),
            },
        )


# Auto-run on import
init_fitness_tables()
