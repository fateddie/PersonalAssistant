"""
Fitness Module (Phase 4)
========================
Workout session controller, exercise logging, and adaptive training.
"""

from .workout_db import init_fitness_tables

# Auto-initialize tables on import
init_fitness_tables()
