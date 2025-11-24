"""
Nutrition UI (Phase 4)
======================
Streamlit UI for meal logging, macro tracking, and nutrition analysis.
"""

import streamlit as st
from datetime import date, timedelta

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
)

# Custom CSS
NUTRITION_CSS = """
<style>
.nutrition-header {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 1rem;
}
.macro-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    color: #1f2937;
}
.macro-number {
    font-size: 1.5rem;
    font-weight: bold;
}
.macro-calories { color: #ef4444; }
.macro-protein { color: #3b82f6; }
.macro-carbs { color: #f59e0b; }
.macro-fat { color: #8b5cf6; }
.meal-card {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    color: #1f2937;
}
.meal-type-badge {
    display: inline-block;
    background: #22c55e;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    text-transform: uppercase;
}
.food-item {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 0.5rem;
    margin: 0.25rem 0;
    font-size: 0.9rem;
    color: #1f2937;
}
.progress-bar {
    height: 8px;
    background: #e2e8f0;
    border-radius: 4px;
    overflow: hidden;
    margin: 0.5rem 0;
}
.progress-fill {
    height: 100%;
    border-radius: 4px;
}
.progress-calories { background: #ef4444; }
.progress-protein { background: #3b82f6; }
.progress-carbs { background: #f59e0b; }
.progress-fat { background: #8b5cf6; }
</style>
"""


def render_nutrition_tab():
    """Main entry point for nutrition tab."""
    st.markdown(NUTRITION_CSS, unsafe_allow_html=True)

    # Initialize session state
    if "nutrition_view" not in st.session_state:
        st.session_state.nutrition_view = "today"
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = date.today()

    # Header
    st.markdown(
        """<div class="nutrition-header">
        <h2 style="margin:0;">Nutrition Tracker</h2>
        <p style="margin:0.5rem 0 0 0; opacity:0.9;">Track meals, hit your macros</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Navigation
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Today", use_container_width=True):
            st.session_state.nutrition_view = "today"
            st.session_state.selected_date = date.today()
            st.rerun()
    with col2:
        if st.button("Log Meal", use_container_width=True):
            st.session_state.nutrition_view = "log"
            st.rerun()
    with col3:
        if st.button("Settings", use_container_width=True):
            st.session_state.nutrition_view = "settings"
            st.rerun()

    st.markdown("---")

    # Render based on view
    if st.session_state.nutrition_view == "today":
        _render_daily_view()
    elif st.session_state.nutrition_view == "log":
        _render_log_meal()
    elif st.session_state.nutrition_view == "settings":
        _render_settings()


def _render_daily_view():
    """Render daily nutrition summary and meals."""
    selected_date = st.session_state.selected_date

    # Date navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("<", use_container_width=True):
            st.session_state.selected_date = selected_date - timedelta(days=1)
            st.rerun()
    with col2:
        st.markdown(f"### {selected_date.strftime('%A, %b %d')}")
    with col3:
        if selected_date < date.today():
            if st.button(">", use_container_width=True):
                st.session_state.selected_date = selected_date + timedelta(days=1)
                st.rerun()

    # Daily summary
    summary = get_daily_summary(selected_date)
    targets = summary["targets"]

    # Macro cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pct = min(100, int(summary["calories"] / targets["calories"] * 100))
        st.markdown(
            f"""<div class="macro-card">
            <div class="macro-number macro-calories">{summary['calories']}</div>
            <div>/ {targets['calories']} cal</div>
            <div class="progress-bar"><div class="progress-fill progress-calories" style="width:{pct}%;"></div></div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col2:
        pct = min(100, int(summary["protein_g"] / targets["protein_g"] * 100))
        st.markdown(
            f"""<div class="macro-card">
            <div class="macro-number macro-protein">{summary['protein_g']:.0f}g</div>
            <div>/ {targets['protein_g']}g protein</div>
            <div class="progress-bar"><div class="progress-fill progress-protein" style="width:{pct}%;"></div></div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col3:
        pct = min(100, int(summary["carbs_g"] / targets["carbs_g"] * 100))
        st.markdown(
            f"""<div class="macro-card">
            <div class="macro-number macro-carbs">{summary['carbs_g']:.0f}g</div>
            <div>/ {targets['carbs_g']}g carbs</div>
            <div class="progress-bar"><div class="progress-fill progress-carbs" style="width:{pct}%;"></div></div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col4:
        pct = min(100, int(summary["fat_g"] / targets["fat_g"] * 100))
        st.markdown(
            f"""<div class="macro-card">
            <div class="macro-number macro-fat">{summary['fat_g']:.0f}g</div>
            <div>/ {targets['fat_g']}g fat</div>
            <div class="progress-bar"><div class="progress-fill progress-fat" style="width:{pct}%;"></div></div>
            </div>""",
            unsafe_allow_html=True,
        )

    # Meals
    st.markdown("---")
    st.subheader("Meals")

    meals = get_meals_for_date(selected_date)

    if not meals:
        st.info("No meals logged yet today. Add your first meal!")
    else:
        for meal in meals:
            type_emoji = {
                "breakfast": "",
                "lunch": "",
                "dinner": "",
                "snack": "",
            }.get(meal["meal_type"], "")

            st.markdown(
                f"""<div class="meal-card">
                <span class="meal-type-badge">{type_emoji} {meal['meal_type']}</span>
                <span style="float:right;">{meal['total_calories']} cal</span>
                </div>""",
                unsafe_allow_html=True,
            )

            for item in meal["items"]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(
                        f"""<div class="food-item">
                        {item['name']} ({item['servings']}x) - {item['calories']} cal
                        <small style="color:#6b7280;"> | P: {item['protein_g']:.0f}g C: {item['carbs_g']:.0f}g F: {item['fat_g']:.0f}g</small>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                with col2:
                    if st.button("X", key=f"del_{item['id']}"):
                        delete_meal_item(item["id"])
                        st.rerun()


def _render_log_meal():
    """Render meal logging form."""
    st.subheader("Log a Meal")

    # Meal type selection
    meal_type = st.selectbox("Meal Type", options=["breakfast", "lunch", "dinner", "snack"])

    meal_date = st.date_input("Date", value=date.today())

    st.markdown("---")

    # Search foods
    st.markdown("### Add Foods")

    search = st.text_input("Search foods", placeholder="Type to search...")

    foods = get_food_items(search=search if search else None)

    # Initialize meal items in session state
    if "current_meal_items" not in st.session_state:
        st.session_state.current_meal_items = []

    # Food selection
    if foods:
        food_options = {
            f"{f['name']} ({f['calories']} cal/{f['serving_size']})": f for f in foods[:20]
        }

        selected_food = st.selectbox("Select food", options=[""] + list(food_options.keys()))

        if selected_food:
            food = food_options[selected_food]
            col1, col2 = st.columns([2, 1])
            with col1:
                servings = st.number_input(
                    "Servings", min_value=0.5, max_value=10.0, value=1.0, step=0.5
                )
            with col2:
                if st.button("Add to Meal"):
                    st.session_state.current_meal_items.append(
                        {
                            "food_id": food["id"],
                            "name": food["name"],
                            "servings": servings,
                            "calories": int(food["calories"] * servings),
                            "protein_g": food["protein_g"] * servings,
                            "carbs_g": food["carbs_g"] * servings,
                            "fat_g": food["fat_g"] * servings,
                        }
                    )
                    st.rerun()

    # Quick add custom food
    with st.expander("Quick Add Custom Food"):
        col1, col2 = st.columns(2)
        with col1:
            custom_name = st.text_input("Food name", key="custom_name")
            custom_cal = st.number_input("Calories", min_value=0, value=100, key="custom_cal")
        with col2:
            custom_protein = st.number_input(
                "Protein (g)", min_value=0.0, value=0.0, key="custom_p"
            )
            custom_carbs = st.number_input("Carbs (g)", min_value=0.0, value=0.0, key="custom_c")
            custom_fat = st.number_input("Fat (g)", min_value=0.0, value=0.0, key="custom_f")

        if st.button("Add Custom Food"):
            if custom_name:
                st.session_state.current_meal_items.append(
                    {
                        "food_id": None,
                        "name": custom_name,
                        "servings": 1,
                        "calories": custom_cal,
                        "protein_g": custom_protein,
                        "carbs_g": custom_carbs,
                        "fat_g": custom_fat,
                    }
                )
                st.rerun()

    # Current meal items
    if st.session_state.current_meal_items:
        st.markdown("---")
        st.markdown("### Current Meal")

        total_cal = 0
        for i, item in enumerate(st.session_state.current_meal_items):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"""<div class="food-item">
                    {item['name']} ({item['servings']}x) - {item['calories']} cal
                    </div>""",
                    unsafe_allow_html=True,
                )
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.current_meal_items.pop(i)
                    st.rerun()
            total_cal += item["calories"]

        st.markdown(f"**Total: {total_cal} calories**")

        # Save meal
        if st.button("Save Meal", type="primary", use_container_width=True):
            meal_id = create_meal(meal_date, meal_type)
            for item in st.session_state.current_meal_items:
                add_food_to_meal(
                    meal_id=meal_id,
                    food_id=item["food_id"],
                    custom_name=item["name"] if not item["food_id"] else None,
                    servings=item["servings"],
                    calories=item["calories"],
                    protein_g=item["protein_g"],
                    carbs_g=item["carbs_g"],
                    fat_g=item["fat_g"],
                )
            st.session_state.current_meal_items = []
            st.success("Meal saved!")
            st.session_state.nutrition_view = "today"
            st.rerun()


def _render_settings():
    """Render nutrition settings."""
    st.subheader("Nutrition Targets")

    targets = get_nutrition_targets()

    with st.form("nutrition_targets"):
        calories = st.number_input(
            "Daily Calories", min_value=1000, max_value=5000, value=targets["calories"]
        )
        protein = st.number_input(
            "Protein (g)", min_value=50, max_value=400, value=targets["protein_g"]
        )
        carbs = st.number_input("Carbs (g)", min_value=50, max_value=500, value=targets["carbs_g"])
        fat = st.number_input("Fat (g)", min_value=20, max_value=200, value=targets["fat_g"])

        if st.form_submit_button("Update Targets", type="primary"):
            update_nutrition_targets(calories, protein, carbs, fat)
            st.success("Targets updated!")
            st.rerun()

    # Weekly summary
    st.markdown("---")
    st.subheader("This Week")

    weekly = get_weekly_nutrition(7)
    if weekly:
        avg_cal = sum(d["calories"] for d in weekly) / len(weekly)
        avg_protein = sum(d["protein_g"] for d in weekly) / len(weekly)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Avg Daily Calories", f"{avg_cal:.0f}")
        with col2:
            st.metric("Avg Daily Protein", f"{avg_protein:.0f}g")
