"""
Meal Logging Module (Phase 4)
=============================
Log meals, track macros, and analyze nutrition.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text

DB_PATH = "assistant/data/memory.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def get_food_items(
    category: Optional[str] = None, search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get food items from database."""
    query = """
        SELECT id, name, brand, serving_size, calories, protein_g, carbs_g, fat_g, fiber_g, category
        FROM food_items
        WHERE 1=1
    """
    params = {}

    if category:
        query += " AND category = :category"
        params["category"] = category

    if search:
        query += " AND name LIKE :search"
        params["search"] = f"%{search}%"

    query += " ORDER BY name"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "brand": row[2],
            "serving_size": row[3],
            "calories": row[4],
            "protein_g": row[5],
            "carbs_g": row[6],
            "fat_g": row[7],
            "fiber_g": row[8],
            "category": row[9],
        }
        for row in rows
    ]


def get_food_item(food_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific food item."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, name, brand, serving_size, calories, protein_g, carbs_g, fat_g, fiber_g, category
                FROM food_items WHERE id = :id
            """
            ),
            {"id": food_id},
        ).fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "brand": row[2],
        "serving_size": row[3],
        "calories": row[4],
        "protein_g": row[5],
        "carbs_g": row[6],
        "fat_g": row[7],
        "fiber_g": row[8],
        "category": row[9],
    }


def add_custom_food(
    name: str,
    calories: int,
    protein_g: float = 0,
    carbs_g: float = 0,
    fat_g: float = 0,
    serving_size: str = "1 serving",
    category: str = "custom",
) -> int:
    """Add a custom food item."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO food_items (name, serving_size, calories, protein_g, carbs_g, fat_g, category, is_custom)
                VALUES (:name, :serving, :cal, :protein, :carbs, :fat, :cat, 1)
            """
            ),
            {
                "name": name,
                "serving": serving_size,
                "cal": calories,
                "protein": protein_g,
                "carbs": carbs_g,
                "fat": fat_g,
                "cat": category,
            },
        )
        row = conn.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]


def create_meal(meal_date: date, meal_type: str, notes: Optional[str] = None) -> int:
    """
    Create a new meal entry.

    Args:
        meal_date: Date of the meal
        meal_type: breakfast, lunch, dinner, or snack
        notes: Optional notes

    Returns:
        The meal ID
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO meals (meal_date, meal_type, notes)
                VALUES (:date, :type, :notes)
            """
            ),
            {"date": meal_date.isoformat(), "type": meal_type, "notes": notes},
        )
        row = conn.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]


def add_food_to_meal(
    meal_id: int,
    food_id: Optional[int] = None,
    custom_name: Optional[str] = None,
    servings: float = 1,
    calories: Optional[int] = None,
    protein_g: Optional[float] = None,
    carbs_g: Optional[float] = None,
    fat_g: Optional[float] = None,
) -> int:
    """
    Add a food item to a meal.

    Args:
        meal_id: The meal ID
        food_id: ID of food from database (optional)
        custom_name: Name for custom/quick entry
        servings: Number of servings
        calories: Override calories
        protein_g: Override protein
        carbs_g: Override carbs
        fat_g: Override fat

    Returns:
        The meal item ID
    """
    # If using a food from database, get its macros
    if food_id and not calories:
        food = get_food_item(food_id)
        if food:
            calories = int(food["calories"] * servings)
            protein_g = food["protein_g"] * servings
            carbs_g = food["carbs_g"] * servings
            fat_g = food["fat_g"] * servings

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO meal_items (meal_id, food_id, custom_name, servings, calories, protein_g, carbs_g, fat_g)
                VALUES (:meal, :food, :name, :servings, :cal, :protein, :carbs, :fat)
            """
            ),
            {
                "meal": meal_id,
                "food": food_id,
                "name": custom_name,
                "servings": servings,
                "cal": calories,
                "protein": protein_g,
                "carbs": carbs_g,
                "fat": fat_g,
            },
        )
        row = conn.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]


def get_meals_for_date(target_date: date) -> List[Dict[str, Any]]:
    """Get all meals for a specific date."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, meal_date, meal_type, notes, created_at
                FROM meals
                WHERE meal_date = :date
                ORDER BY
                    CASE meal_type
                        WHEN 'breakfast' THEN 1
                        WHEN 'lunch' THEN 2
                        WHEN 'dinner' THEN 3
                        WHEN 'snack' THEN 4
                    END
            """
            ),
            {"date": target_date.isoformat()},
        ).fetchall()

    meals = []
    for row in rows:
        meal_id = row[0]
        items = get_meal_items(meal_id)

        total_cal = sum(i["calories"] or 0 for i in items)
        total_protein = sum(i["protein_g"] or 0 for i in items)
        total_carbs = sum(i["carbs_g"] or 0 for i in items)
        total_fat = sum(i["fat_g"] or 0 for i in items)

        meals.append(
            {
                "id": row[0],
                "meal_date": row[1],
                "meal_type": row[2],
                "notes": row[3],
                "created_at": row[4],
                "items": items,
                "total_calories": total_cal,
                "total_protein": total_protein,
                "total_carbs": total_carbs,
                "total_fat": total_fat,
            }
        )

    return meals


def get_meal_items(meal_id: int) -> List[Dict[str, Any]]:
    """Get all items in a meal."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT mi.id, mi.food_id, COALESCE(f.name, mi.custom_name) as name,
                       mi.servings, mi.calories, mi.protein_g, mi.carbs_g, mi.fat_g
                FROM meal_items mi
                LEFT JOIN food_items f ON mi.food_id = f.id
                WHERE mi.meal_id = :meal_id
            """
            ),
            {"meal_id": meal_id},
        ).fetchall()

    return [
        {
            "id": row[0],
            "food_id": row[1],
            "name": row[2],
            "servings": row[3],
            "calories": row[4],
            "protein_g": row[5],
            "carbs_g": row[6],
            "fat_g": row[7],
        }
        for row in rows
    ]


def get_daily_summary(target_date: date) -> Dict[str, Any]:
    """Get nutrition summary for a specific date."""
    meals = get_meals_for_date(target_date)

    total_calories = sum(m["total_calories"] for m in meals)
    total_protein = sum(m["total_protein"] for m in meals)
    total_carbs = sum(m["total_carbs"] for m in meals)
    total_fat = sum(m["total_fat"] for m in meals)

    # Get targets
    targets = get_nutrition_targets()

    return {
        "date": target_date.isoformat(),
        "meals": len(meals),
        "calories": total_calories,
        "protein_g": round(total_protein, 1),
        "carbs_g": round(total_carbs, 1),
        "fat_g": round(total_fat, 1),
        "targets": targets,
        "calories_remaining": targets["calories"] - total_calories,
        "protein_remaining": targets["protein_g"] - total_protein,
    }


def get_nutrition_targets() -> Dict[str, int]:
    """Get current nutrition targets."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT calories, protein_g, carbs_g, fat_g FROM nutrition_targets WHERE active = 1 LIMIT 1"
            )
        ).fetchone()

    if not row:
        return {"calories": 2000, "protein_g": 150, "carbs_g": 200, "fat_g": 65}

    return {
        "calories": row[0],
        "protein_g": row[1],
        "carbs_g": row[2],
        "fat_g": row[3],
    }


def update_nutrition_targets(calories: int, protein_g: int, carbs_g: int, fat_g: int) -> bool:
    """Update nutrition targets."""
    with engine.begin() as conn:
        conn.execute(text("UPDATE nutrition_targets SET active = 0"))
        conn.execute(
            text(
                """
                INSERT INTO nutrition_targets (calories, protein_g, carbs_g, fat_g, active)
                VALUES (:cal, :protein, :carbs, :fat, 1)
            """
            ),
            {"cal": calories, "protein": protein_g, "carbs": carbs_g, "fat": fat_g},
        )
    return True


def get_weekly_nutrition(days: int = 7) -> List[Dict[str, Any]]:
    """Get nutrition data for the past week."""
    results = []
    today = date.today()

    for i in range(days):
        target_date = today - timedelta(days=i)
        summary = get_daily_summary(target_date)
        results.append(summary)

    return results


def delete_meal_item(item_id: int) -> bool:
    """Delete a meal item."""
    with engine.begin() as conn:
        result = conn.execute(text("DELETE FROM meal_items WHERE id = :id"), {"id": item_id})
        return result.rowcount > 0


def delete_meal(meal_id: int) -> bool:
    """Delete a meal and all its items."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM meal_items WHERE meal_id = :id"), {"id": meal_id})
        result = conn.execute(text("DELETE FROM meals WHERE id = :id"), {"id": meal_id})
        return result.rowcount > 0
