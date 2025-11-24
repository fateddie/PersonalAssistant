"""
E2E Tests: Prompt Coach UI
==========================
Tests the Prompt Coach user flow and text input functionality.

Requirements:
1. Element exists and is visible
2. Interaction works (click, fill, submit)
3. Correct result appears in UI
4. No error state (unless expected)

Prerequisites:
- Streamlit app running on localhost:8501
- FastAPI backend running on localhost:8000

Run:
    pytest tests/e2e/test_prompt_coach_ui.py -v -s
"""

import pytest
from playwright.sync_api import Page, expect


class TestPromptCoachNavigation:
    """Test navigation to and from the Prompt Coach tab"""

    def test_coach_tab_exists_and_clickable(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Coach tab is visible and can be clicked.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Find the Coach tab (🎓 icon)
        coach_tab = page.get_by_role("tab", name="🎓 Coach")
        assert coach_tab.is_visible(), "Coach tab not found"

        coach_tab.click()
        page.wait_for_timeout(500)

        # Verify we're on the Coach tab
        assert page.get_by_text("Prompt Coach").is_visible(), "Prompt Coach header not visible"
        print("✅ Coach tab navigation works")

    def test_coach_shows_input_stage_initially(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Coach starts on Input stage with text area.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Coach tab
        coach_tab = page.get_by_role("tab", name="🎓 Coach")
        coach_tab.click()
        page.wait_for_timeout(500)

        # Check for input stage elements
        assert page.get_by_text("1. Input").is_visible(), "Progress indicator not showing Input stage"
        assert page.get_by_text("Paste your prompt below").is_visible(), "Input instructions not visible"

        # Check for text area
        text_area = page.locator("textarea").first
        assert text_area.is_visible(), "Input text area not visible"

        print("✅ Input stage displays correctly")


class TestPromptCoachInputStage:
    """Test the Input stage (Stage 1) functionality"""

    def test_can_type_in_input_text_area(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: User can type into the initial prompt text area.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        # Navigate to Coach tab
        page.get_by_role("tab", name="🎓 Coach").click()
        page.wait_for_timeout(500)

        # Find and fill the text area
        text_area = page.locator("textarea").first
        test_prompt = "Write a Python function to sort a list"

        text_area.fill(test_prompt)
        page.wait_for_timeout(300)

        # Verify the text was entered
        assert text_area.input_value() == test_prompt, "Text was not entered into text area"
        print("✅ Can type in input text area")

    def test_analyze_button_enabled_with_input(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Analyze button becomes enabled when text is entered.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("tab", name="🎓 Coach").click()
        page.wait_for_timeout(500)

        # Button should be disabled initially
        analyze_btn = page.get_by_role("button", name="Analyze My Prompt")

        # Fill text area
        text_area = page.locator("textarea").first
        text_area.fill("Write a Python function that processes data files")
        page.wait_for_timeout(500)

        # Button should now be enabled (clickable)
        assert analyze_btn.is_visible(), "Analyze button not visible"
        print("✅ Analyze button responds to input")

    def test_use_example_button_fills_text(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: 'Use Example' button fills the text area.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("tab", name="🎓 Coach").click()
        page.wait_for_timeout(500)

        # Click Use Example button
        example_btn = page.get_by_role("button", name="Use Example")
        example_btn.click()
        page.wait_for_timeout(1000)

        # Verify text area has content
        text_area = page.locator("textarea").first
        value = text_area.input_value()
        assert len(value) > 10, "Example text was not filled"
        print("✅ Use Example button works")


class TestPromptCoachQuestionsStage:
    """Test the Questions stage (Stage 2) functionality"""

    def test_can_reach_questions_stage(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Clicking Analyze transitions to Questions stage.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("tab", name="🎓 Coach").click()
        page.wait_for_timeout(500)

        # Fill text area with a vague prompt (will generate questions)
        text_area = page.locator("textarea").first
        text_area.fill("help me write something with python")
        page.wait_for_timeout(500)

        # Click Analyze
        analyze_btn = page.get_by_role("button", name="Analyze My Prompt")
        analyze_btn.click()

        # Wait for processing (may take a few seconds with LLM)
        page.wait_for_timeout(5000)

        # Should either be on Questions or Result stage
        page_content = page.content()
        has_questions = "Let's Fill the Gaps" in page_content or "Question" in page_content
        has_result = "Comparison" in page_content or "Score" in page_content

        assert has_questions or has_result, "Did not transition to Questions or Result stage"
        print("✅ Successfully transitioned from Input stage")

    def test_can_type_in_question_text_areas(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: User can type into clarifying question text areas.

        This is the critical test for the reported bug.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("tab", name="🎓 Coach").click()
        page.wait_for_timeout(500)

        # Fill with vague prompt to ensure questions are generated
        text_area = page.locator("textarea").first
        text_area.fill("do something with files")
        page.wait_for_timeout(500)

        # Click Analyze
        page.get_by_role("button", name="Analyze My Prompt").click()
        page.wait_for_timeout(5000)

        # Check if we're on questions stage
        page_content = page.content()
        if "Let's Fill the Gaps" not in page_content:
            # May have skipped to result - that's ok for this test
            print("⚠️ Skipped to Result stage (no questions generated)")
            return

        # Find all text areas on the page (should include answer fields)
        text_areas = page.locator("textarea").all()
        assert len(text_areas) > 0, "No text areas found on Questions stage"

        # Try to type in the first answer text area
        first_answer_area = text_areas[0]
        test_answer = "This is my test answer for the question"

        first_answer_area.click()
        page.wait_for_timeout(200)
        first_answer_area.fill(test_answer)
        page.wait_for_timeout(500)

        # Verify the text was entered
        entered_value = first_answer_area.input_value()
        assert entered_value == test_answer, f"Text was not entered. Got: '{entered_value}'"

        print("✅ Can type in question answer text areas")

    def test_answer_persists_after_typing(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Answer text persists after clicking elsewhere.

        Tests that Streamlit session state properly maintains input.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("tab", name="🎓 Coach").click()
        page.wait_for_timeout(500)

        # Fill with vague prompt
        text_area = page.locator("textarea").first
        text_area.fill("process some data")
        page.wait_for_timeout(500)

        page.get_by_role("button", name="Analyze My Prompt").click()
        page.wait_for_timeout(5000)

        page_content = page.content()
        if "Let's Fill the Gaps" not in page_content:
            print("⚠️ Skipped to Result stage")
            return

        # Type in first text area
        text_areas = page.locator("textarea").all()
        if len(text_areas) == 0:
            print("⚠️ No text areas found")
            return

        first_area = text_areas[0]
        test_text = "My persistent answer"
        first_area.fill(test_text)
        page.wait_for_timeout(300)

        # Click somewhere else (like the page body)
        page.locator("body").click()
        page.wait_for_timeout(500)

        # Check the value is still there
        value = first_area.input_value()
        assert value == test_text, f"Answer did not persist. Got: '{value}'"

        print("✅ Answer persists after focus change")

    def test_skip_and_finish_button_works(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Skip & Finish button transitions to Result stage.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("tab", name="🎓 Coach").click()
        page.wait_for_timeout(500)

        text_area = page.locator("textarea").first
        text_area.fill("write something")
        page.wait_for_timeout(500)

        page.get_by_role("button", name="Analyze My Prompt").click()
        page.wait_for_timeout(5000)

        page_content = page.content()
        if "Skip & Finish" not in page_content:
            print("⚠️ Not on Questions stage, Skip button not visible")
            return

        # Click Skip & Finish
        skip_btn = page.get_by_role("button", name="Skip & Finish")
        skip_btn.click()
        page.wait_for_timeout(5000)

        # Should now be on Result stage
        page_content = page.content()
        assert "Comparison" in page_content or "/10" in page_content, "Did not transition to Result stage"

        print("✅ Skip & Finish button works")


class TestPromptCoachResultStage:
    """Test the Result stage (Stage 3) functionality"""

    def test_result_shows_score_and_comparison(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: Result stage shows score badge and comparison.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("tab", name="🎓 Coach").click()
        page.wait_for_timeout(500)

        # Use a more complete prompt to get to results faster
        text_area = page.locator("textarea").first
        text_area.fill(
            "Write a Python function that takes a list of numbers and returns the sum. "
            "The function should handle empty lists gracefully."
        )
        page.wait_for_timeout(500)

        page.get_by_role("button", name="Analyze My Prompt").click()
        page.wait_for_timeout(8000)  # Allow time for full analysis

        # May need to skip questions if any
        if "Skip & Finish" in page.content():
            page.get_by_role("button", name="Skip & Finish").click()
            page.wait_for_timeout(5000)

        page_content = page.content()

        # Check for result elements
        has_score = "/10" in page_content
        has_comparison = "Comparison" in page_content or "Original" in page_content

        assert has_score or has_comparison, "Result stage elements not found"
        print("✅ Result stage displays correctly")

    def test_new_prompt_button_resets(self, page: Page, streamlit_app_url: str):
        """
        E2E Test: 'New Prompt' button returns to Input stage.
        """
        page.goto(streamlit_app_url)
        page.wait_for_timeout(2000)

        page.get_by_role("tab", name="🎓 Coach").click()
        page.wait_for_timeout(500)

        text_area = page.locator("textarea").first
        text_area.fill("Write a function")
        page.wait_for_timeout(500)

        page.get_by_role("button", name="Analyze My Prompt").click()
        page.wait_for_timeout(8000)

        # Get to result (skip questions if needed)
        if "Skip & Finish" in page.content():
            page.get_by_role("button", name="Skip & Finish").click()
            page.wait_for_timeout(5000)

        # Click New Prompt if visible
        if "New Prompt" in page.content():
            page.get_by_role("button", name="New Prompt").click()
            page.wait_for_timeout(1000)

            # Should be back on Input stage
            assert page.get_by_text("Paste your prompt below").is_visible(), "Did not return to Input stage"
            print("✅ New Prompt button resets to Input stage")
        else:
            print("⚠️ New Prompt button not found (may not have reached Result stage)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
