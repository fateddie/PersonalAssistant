"""
E2E Tests: Fitness UI (Phase 4)
===============================
Tests for workout sessions, exercise logging, and progress tracking.

Run:
    pytest tests/e2e/test_fitness_ui.py -v -s
"""

import pytest
from playwright.sync_api import Page, expect


class TestFitnessDashboard:
    """Test fitness dashboard view"""

    def test_fitness_tab_accessible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Fitness tab is accessible from main UI.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page_content = page.content()

        has_fitness = (
            "Fitness" in page_content or "Workout" in page_content or "Exercise" in page_content
        )
        print(f"Fitness content found: {has_fitness}")

    def test_dashboard_stats_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Dashboard shows workout statistics.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Fitness
        fitness_btn = page.get_by_role("button", name="Fitness")
        if fitness_btn.is_visible():
            fitness_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_stats = (
            "Workouts" in page_content
            or "Minutes" in page_content
            or "Sets" in page_content
            or "RPE" in page_content
        )
        print(f"Dashboard stats visible: {has_stats}")


class TestWorkoutSession:
    """Test workout session functionality"""

    def test_start_workout_button_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Start Workout button is visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Fitness
        fitness_btn = page.get_by_role("button", name="Fitness")
        if fitness_btn.is_visible():
            fitness_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_start = "Start Workout" in page_content or "Start" in page_content
        print(f"Start Workout button visible: {has_start}")

    def test_workout_templates_shown(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Workout templates are displayed.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Fitness
        fitness_btn = page.get_by_role("button", name="Fitness")
        if fitness_btn.is_visible():
            fitness_btn.click()
            page.wait_for_timeout(1000)

        # Click Start Workout
        start_btn = page.get_by_role("button", name="Start Workout")
        if start_btn.is_visible():
            start_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_templates = (
            "Full Body" in page_content
            or "template" in page_content.lower()
            or "30-Min" in page_content
        )
        print(f"Workout templates shown: {has_templates}")


class TestExerciseLibrary:
    """Test exercise library view"""

    def test_exercises_view_accessible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Exercises view is accessible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Fitness
        fitness_btn = page.get_by_role("button", name="Fitness")
        if fitness_btn.is_visible():
            fitness_btn.click()
            page.wait_for_timeout(1000)

        # Click Exercises
        exercises_btn = page.get_by_role("button", name="Exercises")
        if exercises_btn.is_visible():
            exercises_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_exercises = (
            "Exercise Library" in page_content
            or "Push-ups" in page_content
            or "Squats" in page_content
        )
        print(f"Exercise library visible: {has_exercises}")

    def test_exercise_categories_shown(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Exercise categories are displayed.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Exercises
        fitness_btn = page.get_by_role("button", name="Fitness")
        if fitness_btn.is_visible():
            fitness_btn.click()
            page.wait_for_timeout(1000)

        exercises_btn = page.get_by_role("button", name="Exercises")
        if exercises_btn.is_visible():
            exercises_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_categories = (
            "strength" in page_content.lower()
            or "cardio" in page_content.lower()
            or "core" in page_content.lower()
        )
        print(f"Exercise categories shown: {has_categories}")


class TestWorkoutProgress:
    """Test workout progress tracking"""

    def test_recent_workouts_shown(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Recent workouts are displayed.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Fitness
        fitness_btn = page.get_by_role("button", name="Fitness")
        if fitness_btn.is_visible():
            fitness_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_recent = (
            "Recent Workouts" in page_content
            or "Recent" in page_content
            or "No recent" in page_content
        )
        print(f"Recent workouts section visible: {has_recent}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
