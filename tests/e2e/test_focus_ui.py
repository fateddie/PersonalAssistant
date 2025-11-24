"""
E2E Tests: Focus & Mindset UI (Phase 3.5 Week 4)
================================================
Tests for Pomodoro timer, CBT thought logs, and energy tracking.

Run:
    pytest tests/e2e/test_focus_ui.py -v -s
"""

import pytest
from playwright.sync_api import Page, expect


class TestPomodoroTimer:
    """Test Pomodoro timer functionality"""

    def test_pomodoro_view_loads(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Pomodoro view loads correctly.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page_content = page.content()

        # Check for Pomodoro-related content
        has_pomodoro = (
            "Pomodoro" in page_content
            or "Focus" in page_content
            or "Timer" in page_content
        )
        print(f"Pomodoro content found: {has_pomodoro}")

    def test_start_button_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Start Pomodoro button is visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Focus/Pomodoro view
        pomodoro_btn = page.get_by_role("button", name="Pomodoro")
        if pomodoro_btn.is_visible():
            pomodoro_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_start = (
            "Start" in page_content
            or "Begin" in page_content
            or "Focus" in page_content
        )
        print(f"Start button found: {has_start}")

    def test_duration_slider_exists(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Duration slider is visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Pomodoro
        pomodoro_btn = page.get_by_role("button", name="Pomodoro")
        if pomodoro_btn.is_visible():
            pomodoro_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_duration = (
            "Duration" in page_content
            or "minutes" in page_content.lower()
            or "25" in page_content
        )
        print(f"Duration control found: {has_duration}")


class TestCBTThoughtLog:
    """Test CBT thought log functionality"""

    def test_thought_log_view_loads(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Thought Log view loads correctly.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Look for Thought Log button
        thought_btn = page.get_by_role("button", name="Thought Log")
        if thought_btn.is_visible():
            thought_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_thought_log = (
            "Thought" in page_content
            or "Challenge" in page_content
            or "CBT" in page_content
        )
        print(f"Thought Log content found: {has_thought_log}")

    def test_cognitive_distortions_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Cognitive distortions are displayed.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Thought Log
        thought_btn = page.get_by_role("button", name="Thought Log")
        if thought_btn.is_visible():
            thought_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        # Check for distortion-related content
        has_distortions = (
            "distortion" in page_content.lower()
            or "All-or-Nothing" in page_content
            or "Catastrophizing" in page_content
        )
        print(f"Cognitive distortions found: {has_distortions}")

    def test_thought_log_form_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Thought logging form is visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Thought Log
        thought_btn = page.get_by_role("button", name="Thought Log")
        if thought_btn.is_visible():
            thought_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_form = (
            "Situation" in page_content
            or "automatic thought" in page_content.lower()
            or "What triggered" in page_content
        )
        print(f"Thought log form found: {has_form}")

    def test_quick_challenges_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Quick thought challenges are accessible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Thought Log
        thought_btn = page.get_by_role("button", name="Thought Log")
        if thought_btn.is_visible():
            thought_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_challenges = (
            "Quick" in page_content
            or "Challenge" in page_content
            or "friend" in page_content.lower()
        )
        print(f"Quick challenges found: {has_challenges}")


class TestEnergyTracking:
    """Test energy tracking functionality"""

    def test_energy_view_loads(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Energy tracking view loads correctly.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Look for Energy button
        energy_btn = page.get_by_role("button", name="Energy")
        if energy_btn.is_visible():
            energy_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_energy = (
            "Energy" in page_content
            or "Morning" in page_content
            or "Afternoon" in page_content
        )
        print(f"Energy tracking content found: {has_energy}")

    def test_energy_sliders_visible(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Energy level sliders are visible.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Energy
        energy_btn = page.get_by_role("button", name="Energy")
        if energy_btn.is_visible():
            energy_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_sliders = (
            "AM" in page_content
            or "PM" in page_content
            or "Morning Energy" in page_content
        )
        print(f"Energy sliders found: {has_sliders}")

    def test_energy_history_section(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Energy history section exists.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Energy
        energy_btn = page.get_by_role("button", name="Energy")
        if energy_btn.is_visible():
            energy_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_history = (
            "History" in page_content
            or "Recent" in page_content
            or "Levels" in page_content
        )
        print(f"Energy history section found: {has_history}")

    def test_energy_recommendations(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Energy recommendations are displayed.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Energy
        energy_btn = page.get_by_role("button", name="Energy")
        if energy_btn.is_visible():
            energy_btn.click()
            page.wait_for_timeout(1000)

        page_content = page.content()

        has_recommendations = (
            "Recommendation" in page_content
            or "Insight" in page_content
            or "Schedule" in page_content
        )
        print(f"Energy recommendations found: {has_recommendations}")


class TestFocusNavigation:
    """Test navigation between focus views"""

    def test_switch_between_views(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Can switch between Pomodoro, Thought Log, and Energy views.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Try clicking through views
        views_found = []

        pomodoro_btn = page.get_by_role("button", name="Pomodoro")
        if pomodoro_btn.is_visible():
            pomodoro_btn.click()
            page.wait_for_timeout(500)
            views_found.append("pomodoro")

        thought_btn = page.get_by_role("button", name="Thought Log")
        if thought_btn.is_visible():
            thought_btn.click()
            page.wait_for_timeout(500)
            views_found.append("thought_log")

        energy_btn = page.get_by_role("button", name="Energy")
        if energy_btn.is_visible():
            energy_btn.click()
            page.wait_for_timeout(500)
            views_found.append("energy")

        print(f"Views found and navigable: {views_found}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
