"""
Nutrition Database Initialization (Phase 4)
===========================================
Creates meal logging and food database tables.
"""

from sqlalchemy import create_engine, text
from pathlib import Path

DB_PATH = "assistant/data/memory.db"


def init_nutrition_tables():
    """Create all Phase 4 nutrition tables if they don't exist."""
    engine = create_engine(f"sqlite:///{DB_PATH}")

    Path("assistant/data").mkdir(parents=True, exist_ok=True)

    with engine.begin() as conn:
        # Food items database
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS food_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                brand TEXT,
                serving_size TEXT DEFAULT '100g',
                calories INTEGER NOT NULL,
                protein_g REAL DEFAULT 0,
                carbs_g REAL DEFAULT 0,
                fat_g REAL DEFAULT 0,
                fiber_g REAL DEFAULT 0,
                category TEXT,
                is_custom INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Meals (breakfast, lunch, dinner, snack)
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_date DATE NOT NULL,
                meal_type TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Meal items (foods in a meal)
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS meal_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_id INTEGER NOT NULL,
                food_id INTEGER,
                custom_name TEXT,
                servings REAL DEFAULT 1,
                calories INTEGER,
                protein_g REAL,
                carbs_g REAL,
                fat_g REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meal_id) REFERENCES meals(id),
                FOREIGN KEY (food_id) REFERENCES food_items(id)
            )
        """
            )
        )

        # Daily nutrition targets
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS nutrition_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calories INTEGER DEFAULT 2000,
                protein_g INTEGER DEFAULT 150,
                carbs_g INTEGER DEFAULT 200,
                fat_g INTEGER DEFAULT 65,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Seed common foods
        foods = [
            # Proteins
            ("Chicken Breast", None, "100g", 165, 31, 0, 3.6, 0, "protein"),
            ("Eggs", None, "1 large", 78, 6, 0.6, 5, 0, "protein"),
            ("Salmon", None, "100g", 208, 20, 0, 13, 0, "protein"),
            ("Greek Yogurt", None, "170g", 100, 17, 6, 0.7, 0, "dairy"),
            ("Cottage Cheese", None, "100g", 98, 11, 3.4, 4.3, 0, "dairy"),
            ("Tuna", None, "100g", 132, 28, 0, 1, 0, "protein"),
            ("Beef (lean)", None, "100g", 250, 26, 0, 15, 0, "protein"),
            ("Tofu", None, "100g", 76, 8, 1.9, 4.8, 0.3, "protein"),
            # Carbs
            ("Rice (cooked)", None, "100g", 130, 2.7, 28, 0.3, 0.4, "grain"),
            ("Oats", None, "100g", 389, 16.9, 66, 6.9, 10.6, "grain"),
            ("Sweet Potato", None, "100g", 86, 1.6, 20, 0.1, 3, "vegetable"),
            ("Banana", None, "1 medium", 105, 1.3, 27, 0.4, 3.1, "fruit"),
            ("Apple", None, "1 medium", 95, 0.5, 25, 0.3, 4.4, "fruit"),
            ("Bread (whole wheat)", None, "1 slice", 81, 4, 14, 1.1, 1.9, "grain"),
            ("Pasta (cooked)", None, "100g", 131, 5, 25, 1.1, 1.8, "grain"),
            # Fats
            ("Avocado", None, "1 medium", 322, 4, 17, 29, 13.5, "fat"),
            ("Almonds", None, "28g", 164, 6, 6, 14, 3.5, "nut"),
            ("Peanut Butter", None, "2 tbsp", 188, 8, 6, 16, 2, "nut"),
            ("Olive Oil", None, "1 tbsp", 119, 0, 0, 13.5, 0, "fat"),
            # Vegetables
            ("Broccoli", None, "100g", 34, 2.8, 7, 0.4, 2.6, "vegetable"),
            ("Spinach", None, "100g", 23, 2.9, 3.6, 0.4, 2.2, "vegetable"),
            ("Carrots", None, "100g", 41, 0.9, 10, 0.2, 2.8, "vegetable"),
            # Dairy
            ("Milk (whole)", None, "240ml", 149, 8, 12, 8, 0, "dairy"),
            ("Milk (skim)", None, "240ml", 83, 8, 12, 0.2, 0, "dairy"),
            ("Cheese (cheddar)", None, "28g", 113, 7, 0.4, 9, 0, "dairy"),
        ]

        for name, brand, serving, cal, protein, carbs, fat, fiber, cat in foods:
            conn.execute(
                text(
                    """
                    INSERT OR IGNORE INTO food_items
                    (name, brand, serving_size, calories, protein_g, carbs_g, fat_g, fiber_g, category)
                    VALUES (:name, :brand, :serving, :cal, :protein, :carbs, :fat, :fiber, :cat)
                """
                ),
                {
                    "name": name,
                    "brand": brand,
                    "serving": serving,
                    "cal": cal,
                    "protein": protein,
                    "carbs": carbs,
                    "fat": fat,
                    "fiber": fiber,
                    "cat": cat,
                },
            )

        # Seed default nutrition targets
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO nutrition_targets (id, calories, protein_g, carbs_g, fat_g, active)
                VALUES (1, 2000, 150, 200, 65, 1)
            """
            )
        )


# Auto-run on import
init_nutrition_tables()
