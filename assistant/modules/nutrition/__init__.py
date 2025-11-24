"""
Nutrition Module (Phase 4)
==========================
Meal logging, macro tracking, and nutrition analysis.
"""

from .nutrition_db import init_nutrition_tables

# Auto-initialize tables on import
init_nutrition_tables()
