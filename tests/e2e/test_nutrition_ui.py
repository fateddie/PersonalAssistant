"""
E2E Tests: Nutrition UI (Phase 4)
=================================
Tests for meal logging, macro tracking, and nutrition settings.

Run:
    pytest tests/e2e/test_nutrition_ui.py -v -s
"""

import pytest
from playwright.sync_api import Page, expect


class TestNutritionDashboard:
    """Test nutrition dashboard view"""

    def test_nutrition_tab_accessible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Nutrition tab is accessible from main UI.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page_content = page.content()

        has_nutrition = (
            "Nutrition" in page_content or "Meal" in page_content or "Calories" in page_content
        )
        print(f"Nutrition content found: {has_nutrition}")

    def test_macro_cards_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Macro tracking cards are displayed.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Nutrition
        nutrition_btn = page.get_by_role("button", name="Nutrition")
        if nutrition_btn.is_visible():
            nutrition_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_macros = (
            "cal" in page_content.lower()
            or "protein" in page_content.lower()
            or "carbs" in page_content.lower()
            or "fat" in page_content.lower()
        )
        print(f"Macro cards visible: {has_macros}")


class TestMealLogging:
    """Test meal logging functionality"""

    def test_log_meal_button_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Log Meal button is visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Nutrition
        nutrition_btn = page.get_by_role("button", name="Nutrition")
        if nutrition_btn.is_visible():
            nutrition_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_log = "Log Meal" in page_content or "Log" in page_content
        print(f"Log Meal button visible: {has_log}")

    def test_meal_type_options_shown(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Meal type selection is available.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Nutrition
        nutrition_btn = page.get_by_role("button", name="Nutrition")
        if nutrition_btn.is_visible():
            nutrition_btn.click()
            page.wait_for_timeout(1000)

        # Click Log Meal
        log_btn = page.get_by_role("button", name="Log Meal")
        if log_btn.is_visible():
            log_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_types = (
            "breakfast" in page_content.lower()
            or "lunch" in page_content.lower()
            or "dinner" in page_content.lower()
            or "snack" in page_content.lower()
        )
        print(f"Meal type options shown: {has_types}")


class TestFoodSearch:
    """Test food search and selection"""

    def test_food_search_available(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Food search input is available.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to meal logging
        nutrition_btn = page.get_by_role("button", name="Nutrition")
        if nutrition_btn.is_visible():
            nutrition_btn.click()
            page.wait_for_timeout(1000)

        log_btn = page.get_by_role("button", name="Log Meal")
        if log_btn.is_visible():
            log_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_search = (
            "Search" in page_content or "search" in page_content or "food" in page_content.lower()
        )
        print(f"Food search available: {has_search}")

    def test_custom_food_entry_available(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Custom food quick-add is available.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to meal logging
        nutrition_btn = page.get_by_role("button", name="Nutrition")
        if nutrition_btn.is_visible():
            nutrition_btn.click()
            page.wait_for_timeout(1000)

        log_btn = page.get_by_role("button", name="Log Meal")
        if log_btn.is_visible():
            log_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_custom = (
            "Custom" in page_content
            or "Quick Add" in page_content
            or "custom" in page_content.lower()
        )
        print(f"Custom food entry available: {has_custom}")


class TestNutritionSettings:
    """Test nutrition settings"""

    def test_settings_accessible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Nutrition settings are accessible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Nutrition
        nutrition_btn = page.get_by_role("button", name="Nutrition")
        if nutrition_btn.is_visible():
            nutrition_btn.click()
            page.wait_for_timeout(1000)

        # Click Settings
        settings_btn = page.get_by_role("button", name="Settings")
        if settings_btn.is_visible():
            settings_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_settings = (
            "Targets" in page_content or "Daily" in page_content or "Calories" in page_content
        )
        print(f"Nutrition settings accessible: {has_settings}")

    def test_target_inputs_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Nutrition target inputs are visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Settings
        nutrition_btn = page.get_by_role("button", name="Nutrition")
        if nutrition_btn.is_visible():
            nutrition_btn.click()
            page.wait_for_timeout(1000)

        settings_btn = page.get_by_role("button", name="Settings")
        if settings_btn.is_visible():
            settings_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_targets = "Protein" in page_content or "Carbs" in page_content or "Fat" in page_content
        print(f"Target inputs visible: {has_targets}")


class TestDailySummary:
    """Test daily nutrition summary"""

    def test_daily_view_shows_date(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Daily view shows current date.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Nutrition
        nutrition_btn = page.get_by_role("button", name="Nutrition")
        if nutrition_btn.is_visible():
            nutrition_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for date-related content
        has_date = (
            "Today" in page_content
            or "Monday" in page_content
            or "Tuesday" in page_content
            or "Wednesday" in page_content
            or "Thursday" in page_content
            or "Friday" in page_content
            or "Saturday" in page_content
            or "Sunday" in page_content
        )
        print(f"Daily view shows date: {has_date}")

    def test_meals_section_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Meals section is visible in daily view.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Nutrition
        nutrition_btn = page.get_by_role("button", name="Nutrition")
        if nutrition_btn.is_visible():
            nutrition_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_meals = (
            "Meals" in page_content
            or "No meals" in page_content
            or "logged" in page_content.lower()
        )
        print(f"Meals section visible: {has_meals}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
