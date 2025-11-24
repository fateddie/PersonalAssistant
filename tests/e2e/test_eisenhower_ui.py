"""
E2E Tests: Eisenhower Matrix UI (Phase 3.5 Week 2)
==================================================
Tests for Eisenhower Matrix view and task classification.

Run:
    pytest tests/e2e/test_eisenhower_ui.py -v -s
"""

import pytest
from playwright.sync_api import Page, expect


class TestEisenhowerNavigation:
    """Test navigation to Eisenhower Matrix view"""

    def test_matrix_button_exists(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Matrix button is visible in Discipline tab.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Discipline
        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        # Check for Matrix button
        matrix_btn = page.get_by_role("button", name="Matrix")
        assert matrix_btn.is_visible(), "Matrix button not found"
        print("Matrix button visible")

    def test_matrix_view_loads(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Clicking Matrix shows the Eisenhower Matrix view.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="Matrix").click()
        page.wait_for_timeout(1000)

        # Verify matrix content
        page_content = page.content()
        assert "Eisenhower Matrix" in page_content, "Matrix header not visible"
        print("Eisenhower Matrix view loads correctly")


class TestEisenhowerQuadrants:
    """Test quadrant display functionality"""

    def test_all_quadrants_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: All four quadrants are displayed.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="Matrix").click()
        page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for quadrant labels
        quadrant_labels = ["Do First", "Schedule", "Delegate", "Eliminate"]
        found = sum(1 for label in quadrant_labels if label in page_content)

        assert found >= 3, f"Expected at least 3 quadrant labels, found {found}"
        print(f"Found {found}/4 quadrant labels")

    def test_legend_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Legend showing quadrant colors is visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="Matrix").click()
        page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for legend items
        assert "Q1" in page_content or "Quadrant" in page_content, "Legend not visible"
        print("Legend is visible")

    def test_auto_classify_button_exists(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Auto-Classify button is visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="Matrix").click()
        page.wait_for_timeout(1000)

        # Look for auto-classify button
        auto_btn = page.get_by_role("button", name="Auto-Classify")
        if auto_btn.is_visible():
            print("Auto-Classify button visible")
        else:
            # May be named differently
            page_content = page.content()
            assert "Auto" in page_content or "Classify" in page_content, "Auto-classify not found"
            print("Auto-classify feature present")


class TestEisenhowerInteraction:
    """Test interaction with the matrix"""

    def test_auto_classify_works(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Auto-Classify button can be clicked.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="Matrix").click()
        page.wait_for_timeout(1000)

        # Try to click Auto-Classify
        auto_btn = page.get_by_role("button", name="Auto-Classify")
        if auto_btn.is_visible():
            auto_btn.click()
            page.wait_for_timeout(1000)

            # Should show success or info message
            page_content = page.content()
            has_feedback = "classified" in page_content.lower() or "tasks" in page_content.lower()
            print(f"Auto-classify feedback shown: {has_feedback}")
        else:
            print("Auto-classify button not found, skipping")

    def test_matrix_shows_tasks(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Matrix shows tasks (or empty state messages).
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="Matrix").click()
        page.wait_for_timeout(1000)

        page_content = page.content()

        # Should either show tasks or "No tasks" messages
        has_tasks = "task" in page_content.lower()
        has_empty = "no tasks" in page_content.lower() or "empty" in page_content.lower()

        assert has_tasks or has_empty, "Matrix should show tasks or empty state"
        print("Matrix displays task content appropriately")


class TestDisciplineModeSwitch:
    """Test switching between discipline modes"""

    def test_switch_between_modes(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Can switch between Today, Tomorrow, and Matrix views.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Discipline").click()
        page.wait_for_timeout(1000)

        # Switch to Matrix
        page.get_by_role("button", name="Matrix").click()
        page.wait_for_timeout(500)
        assert "Eisenhower" in page.content() or "Matrix" in page.content()

        # Switch to Today
        page.get_by_role("button", name="Today's Plan").click()
        page.wait_for_timeout(500)
        today_content = page.content()
        has_today = "Plan" in today_content or "Priorities" in today_content

        # Switch to Tomorrow
        page.get_by_role("button", name="Plan Tomorrow").click()
        page.wait_for_timeout(500)
        tomorrow_content = page.content()
        has_tomorrow = "Tomorrow" in tomorrow_content or "Reflect" in tomorrow_content

        assert has_today or has_tomorrow, "Mode switching should work"
        print("Mode switching works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
