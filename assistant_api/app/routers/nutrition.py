"""
Nutrition API Router (Phase 4)
==============================
Endpoints for meal logging, food database, and macro tracking.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from assistant.modules.nutrition.meal_logging import (
    get_food_items,
    get_food_item,
    add_custom_food,
    create_meal,
    add_food_to_meal,
    get_meals_for_date,
    get_daily_summary,
    get_nutrition_targets,
    update_nutrition_targets,
    get_weekly_nutrition,
    delete_meal_item,
    delete_meal,
)

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


# ============ Pydantic Models ============


class CustomFoodCreate(BaseModel):
    """Create a custom food item."""

    name: str
    calories: int = Field(..., ge=0)
    protein_g: float = Field(default=0, ge=0)
    carbs_g: float = Field(default=0, ge=0)
    fat_g: float = Field(default=0, ge=0)
    serving_size: str = "1 serving"
    category: str = "custom"


class MealCreate(BaseModel):
    """Create a meal."""

    meal_date: date
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack)$")
    notes: Optional[str] = None


class MealItemAdd(BaseModel):
    """Add item to meal."""

    food_id: Optional[int] = None
    custom_name: Optional[str] = None
    servings: float = Field(default=1, gt=0)
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None


class NutritionTargets(BaseModel):
    """Nutrition targets."""

    calories: int = Field(..., ge=1000, le=5000)
    protein_g: int = Field(..., ge=50, le=400)
    carbs_g: int = Field(..., ge=50, le=500)
    fat_g: int = Field(..., ge=20, le=200)


# ============ Food Endpoints ============


@router.get("/foods")
async def list_foods(category: Optional[str] = None, search: Optional[str] = None):
    """Get food items from database."""
    foods = get_food_items(category=category, search=search)
    return {"foods": foods}


@router.get("/foods/{food_id}")
async def get_food(food_id: int):
    """Get a specific food item."""
    food = get_food_item(food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    return food


@router.post("/foods")
async def create_food(food: CustomFoodCreate):
    """Add a custom food item."""
    food_id = add_custom_food(
        name=food.name,
        calories=food.calories,
        protein_g=food.protein_g,
        carbs_g=food.carbs_g,
        fat_g=food.fat_g,
        serving_size=food.serving_size,
        category=food.category,
    )
    return {"food_id": food_id, "success": True}


# ============ Meal Endpoints ============


@router.post("/meals")
async def create_new_meal(meal: MealCreate):
    """Create a new meal entry."""
    meal_id = create_meal(meal.meal_date, meal.meal_type, meal.notes)
    return {"meal_id": meal_id, "success": True}


@router.post("/meals/{meal_id}/items")
async def add_item_to_meal(meal_id: int, item: MealItemAdd):
    """Add a food item to a meal."""
    item_id = add_food_to_meal(
        meal_id=meal_id,
        food_id=item.food_id,
        custom_name=item.custom_name,
        servings=item.servings,
        calories=item.calories,
        protein_g=item.protein_g,
        carbs_g=item.carbs_g,
        fat_g=item.fat_g,
    )
    return {"item_id": item_id, "success": True}


@router.get("/meals/{target_date}")
async def get_meals(target_date: date):
    """Get all meals for a specific date."""
    meals = get_meals_for_date(target_date)
    return {"meals": meals}


@router.delete("/meals/{meal_id}")
async def remove_meal(meal_id: int):
    """Delete a meal."""
    success = delete_meal(meal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meal not found")
    return {"success": True}


@router.delete("/meals/items/{item_id}")
async def remove_meal_item(item_id: int):
    """Delete a meal item."""
    success = delete_meal_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"success": True}


# ============ Summary Endpoints ============


@router.get("/summary/{target_date}")
async def daily_summary(target_date: date):
    """Get nutrition summary for a specific date."""
    summary = get_daily_summary(target_date)
    return summary


@router.get("/summary/weekly")
async def weekly_summary(days: int = 7):
    """Get weekly nutrition summary."""
    weekly = get_weekly_nutrition(days)
    return {"weekly": weekly}


# ============ Targets Endpoints ============


@router.get("/targets")
async def get_targets():
    """Get current nutrition targets."""
    targets = get_nutrition_targets()
    return targets


@router.put("/targets")
async def set_targets(targets: NutritionTargets):
    """Update nutrition targets."""
    success = update_nutrition_targets(
        calories=targets.calories,
        protein_g=targets.protein_g,
        carbs_g=targets.carbs_g,
        fat_g=targets.fat_g,
    )
    return {"success": success}
