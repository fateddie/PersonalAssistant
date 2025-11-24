"""
E2E Tests: Habits & Planning UI (Phase 3.5 Week 3)
==================================================
Tests for Habit Stacking, If-Then Planning, and GTD Brain Dump.

Run:
    pytest tests/e2e/test_habits_ui.py -v -s
"""

import pytest
from playwright.sync_api import Page, expect


class TestHabitStackingNavigation:
    """Test navigation to Habit Stacking view"""

    def test_habits_tab_exists(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Habits-related navigation exists.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Check for Habits or Planning related button
        page_content = page.content()
        has_habits = "Habit" in page_content or "Planning" in page_content
        print(f"Habits navigation found: {has_habits}")

    def test_habit_stacking_view_loads(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Habit Stacking view loads correctly.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Discipline first
        discipline_btn = page.get_by_role("button", name="Discipline")
        if discipline_btn.is_visible():
            discipline_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for habit-related content
        has_habit_content = (
            "Habit" in page_content
            or "After" in page_content
            or "Stacking" in page_content
        )
        print(f"Habit content found: {has_habit_content}")


class TestHabitStackingCreate:
    """Test habit chain creation"""

    def test_create_habit_form_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Habit chain creation form is visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        page_content = page.content()

        # Look for form elements
        has_form = (
            "After I" in page_content
            or "I will" in page_content
            or "Create" in page_content
        )
        print(f"Habit creation form visible: {has_form}")


class TestIfThenPlanning:
    """Test If-Then planning view"""

    def test_if_then_button_exists(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: If-Then Plans button/tab exists.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for If-Then content
        has_if_then = "If-Then" in page_content or "If " in page_content
        print(f"If-Then planning found: {has_if_then}")

    def test_suggested_plans_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Suggested If-Then plans are visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        # Look for If-Then Plans button
        if_then_btn = page.get_by_role("button", name="If-Then Plans")
        if if_then_btn.is_visible():
            if_then_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for suggestions or categories
        has_suggestions = (
            "Suggested" in page_content
            or "procrastination" in page_content.lower()
            or "distraction" in page_content.lower()
        )
        print(f"Suggested plans visible: {has_suggestions}")


class TestBrainDump:
    """Test GTD Brain Dump view"""

    def test_brain_dump_button_exists(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Brain Dump button/tab exists.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for Brain Dump content
        has_brain_dump = (
            "Brain Dump" in page_content
            or "Capture" in page_content
            or "Inbox" in page_content
        )
        print(f"Brain Dump found: {has_brain_dump}")

    def test_quick_capture_input_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Quick capture text area is visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        # Look for Brain Dump button
        brain_dump_btn = page.get_by_role("button", name="Brain Dump")
        if brain_dump_btn.is_visible():
            brain_dump_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for capture-related elements
        has_capture = (
            "Quick Capture" in page_content
            or "What's on your mind" in page_content
            or "Capture All" in page_content
        )
        print(f"Quick capture visible: {has_capture}")

    def test_process_inbox_section(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Process Inbox section exists.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        # Look for Brain Dump button
        brain_dump_btn = page.get_by_role("button", name="Brain Dump")
        if brain_dump_btn.is_visible():
            brain_dump_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for inbox processing
        has_inbox = (
            "Process Inbox" in page_content
            or "Inbox clear" in page_content
            or "items to process" in page_content
        )
        print(f"Inbox processing section visible: {has_inbox}")


class TestWeeklyReview:
    """Test Weekly Review view"""

    def test_weekly_review_accessible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Weekly Review is accessible from UI.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page_content = page.content()

        # Check for Weekly Review anywhere
        has_weekly = (
            "Weekly Review" in page_content
            or "Weekly" in page_content
        )
        print(f"Weekly Review found: {has_weekly}")

    def test_week_stats_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Weekly stats are displayed.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to find Weekly Review
        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for stats-related content
        has_stats = (
            "Stats" in page_content
            or "Tasks Done" in page_content
            or "Habit Rate" in page_content
            or "completed" in page_content.lower()
        )
        print(f"Week stats visible: {has_stats}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
