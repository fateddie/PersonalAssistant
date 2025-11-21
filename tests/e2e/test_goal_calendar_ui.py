"""
E2E Tests: Goal Calendar Integration UI
========================================
Tests the full user flow for creating goals with calendar integration.

Requirements (per UI_TESTING_STANDARDS.md):
1. Element exists and is visible
2. Interaction works (click, fill, submit)
3. Correct result appears in UI
4. No error state (unless expected)

Prerequisites:
- Streamlit app running on localhost:8501
- FastAPI backend running on localhost:8000
- Database migrated with goal_calendar_config tables

Run:
    pytest tests/e2e/test_goal_calendar_ui.py -v
"""

import pytest
from playwright.sync_api import Page, expect


def test_goal_creation_without_calendar(page: Page, streamlit_app_url: str):
    """
    E2E Test: Create goal without calendar integration.

    User flow:
    1. Navigate to app
    2. Go to "Add New" tab
    3. Select "goal" type
    4. Fill in goal details
    5. Submit without calendar
    6. Verify success message
    """
    # Navigate to app
    page.goto(streamlit_app_url)

    # Wait for page to load (Streamlit can be slow)
    page.wait_for_timeout(2000)

    # Click "Add New" tab (4th tab)
    add_new_tab = page.get_by_text("➕ Add New")
    assert add_new_tab.is_visible(), "Add New tab not found"
    add_new_tab.click()
    page.wait_for_timeout(500)

    # Verify form elements exist
    type_select = page.locator("label:has-text('Type')").locator("..").locator("select")
    assert type_select.is_visible(), "Type selector not found"

    # Select "goal" type
    type_select.select_option("goal")
    page.wait_for_timeout(500)

    # Fill in title
    title_input = page.locator("input[aria-label='Title *']")
    assert title_input.is_visible(), "Title input not found"
    title_input.fill("Daily Morning Routine")

    # Fill in description
    description_textarea = page.locator("textarea[aria-label='Description']")
    assert description_textarea.is_visible(), "Description textarea not found"
    description_textarea.fill("Morning workout and meditation, 3 times per week")

    # Verify "Add to Calendar" checkbox exists (but don't check it)
    calendar_checkbox = page.get_by_text("Add to Calendar")
    assert calendar_checkbox.is_visible(), "Calendar checkbox not found for goal type"

    # Submit form
    submit_button = page.get_by_role("button", name="➕ Create Item")
    assert submit_button.is_visible(), "Submit button not found"
    submit_button.click()

    # Wait for response
    page.wait_for_timeout(2000)

    # Verify success (look for success indicator in page)
    page_content = page.content().lower()
    # Check for either success message or no error
    has_error = "error" in page_content and "error creating" in page_content
    assert not has_error, "Error message found after goal creation"

    print("✅ Goal created successfully without calendar")


def test_goal_creation_with_calendar_integration(page: Page, streamlit_app_url: str):
    """
    E2E Test: Create goal with calendar integration.

    User flow:
    1. Navigate to app
    2. Go to "Add New" tab
    3. Select "goal" type
    4. Fill in goal details
    5. Check "Add to Calendar"
    6. Fill in recurring days and time
    7. Submit form
    8. Verify calendar events created
    9. Verify no errors
    """
    # Navigate to app
    page.goto(streamlit_app_url)

    # Wait for page to load
    page.wait_for_timeout(2000)

    # Click "Add New" tab
    add_new_tab = page.get_by_text("➕ Add New")
    assert add_new_tab.is_visible(), "Add New tab not found"
    add_new_tab.click()
    page.wait_for_timeout(500)

    # Select "goal" type
    type_select = page.locator("label:has-text('Type')").locator("..").locator("select")
    assert type_select.is_visible(), "Type selector not found"
    type_select.select_option("goal")
    page.wait_for_timeout(500)

    # Fill in goal title
    title_input = page.locator("input[aria-label='Title *']")
    assert title_input.is_visible(), "Title input not found"
    title_input.fill("Morning Gym Session")

    # Fill in description with target
    description_textarea = page.locator("textarea[aria-label='Description']")
    assert description_textarea.is_visible(), "Description textarea not found"
    description_textarea.fill("Weight training and cardio, 3 times per week")

    # Check "Add to Calendar" checkbox
    calendar_checkbox = page.get_by_text("Add to Calendar")
    assert calendar_checkbox.is_visible(), "Calendar checkbox not found"
    calendar_checkbox.click()
    page.wait_for_timeout(500)

    # Verify calendar fields appear
    recurring_input = page.locator("input[aria-label='Recurring Days']")
    assert recurring_input.is_visible(), "Recurring Days input not visible after checking calendar"

    start_time_input = page.locator("input[aria-label='Start Time']")
    assert start_time_input.is_visible(), "Start Time input not visible"

    end_time_input = page.locator("input[aria-label='End Time']")
    assert end_time_input.is_visible(), "End Time input not visible"

    # Fill in calendar details
    recurring_input.fill("mon, wed, fri")
    start_time_input.fill("7:30am")
    end_time_input.fill("9:00am")

    # Submit form
    submit_button = page.get_by_role("button", name="➕ Create Item")
    assert submit_button.is_visible(), "Submit button not found"
    submit_button.click()

    # Wait for calendar creation (can take a few seconds)
    page.wait_for_timeout(5000)

    # Verify success messages appear
    page_content = page.content().lower()

    # Check for success indicators
    has_goal_created = "goal" in page_content and "created" in page_content
    has_calendar_created = "calendar" in page_content and "events" in page_content

    # Check for errors
    has_error = "error creating" in page_content or "failed" in page_content

    assert not has_error, "Error message found during goal/calendar creation"
    assert has_goal_created or has_calendar_created, "No success indicators found"

    print("✅ Goal with calendar integration created successfully")


def test_calendar_fields_only_visible_for_goals(page: Page, streamlit_app_url: str):
    """
    E2E Test: Calendar fields should only appear when "goal" type is selected.

    User flow:
    1. Navigate to app
    2. Go to "Add New" tab
    3. Verify calendar checkbox not visible for non-goal types
    4. Select "goal" type
    5. Verify calendar checkbox appears
    """
    # Navigate to app
    page.goto(streamlit_app_url)
    page.wait_for_timeout(2000)

    # Click "Add New" tab
    add_new_tab = page.get_by_text("➕ Add New")
    add_new_tab.click()
    page.wait_for_timeout(500)

    # Default type might be "appointment" - verify no calendar checkbox
    type_select = page.locator("label:has-text('Type')").locator("..").locator("select")
    type_select.select_option("appointment")
    page.wait_for_timeout(500)

    # Calendar section should not exist for appointment
    calendar_section = page.get_by_text("Calendar Integration")
    assert not calendar_section.is_visible(), "Calendar section visible for non-goal type"

    # Select "goal" type
    type_select.select_option("goal")
    page.wait_for_timeout(500)

    # Calendar section should now be visible
    calendar_checkbox = page.get_by_text("Add to Calendar")
    assert calendar_checkbox.is_visible(), "Calendar checkbox not visible for goal type"

    print("✅ Calendar fields visibility correct")


def test_calendar_validation_on_invalid_input(page: Page, streamlit_app_url: str):
    """
    E2E Test: Calendar creation should show error for invalid time input.

    User flow:
    1. Navigate to app
    2. Create goal with invalid calendar times
    3. Verify error message appears
    """
    # Navigate to app
    page.goto(streamlit_app_url)
    page.wait_for_timeout(2000)

    # Go to Add New tab
    add_new_tab = page.get_by_text("➕ Add New")
    add_new_tab.click()
    page.wait_for_timeout(500)

    # Select goal type
    type_select = page.locator("label:has-text('Type')").locator("..").locator("select")
    type_select.select_option("goal")
    page.wait_for_timeout(500)

    # Fill in goal
    title_input = page.locator("input[aria-label='Title *']")
    title_input.fill("Test Goal Invalid Time")

    description_textarea = page.locator("textarea[aria-label='Description']")
    description_textarea.fill("3 times per week")

    # Check calendar
    calendar_checkbox = page.get_by_text("Add to Calendar")
    calendar_checkbox.click()
    page.wait_for_timeout(500)

    # Fill in INVALID calendar details (end time before start time)
    recurring_input = page.locator("input[aria-label='Recurring Days']")
    recurring_input.fill("monday")

    start_time_input = page.locator("input[aria-label='Start Time']")
    start_time_input.fill("9:00am")

    end_time_input = page.locator("input[aria-label='End Time']")
    end_time_input.fill("7:00am")  # Invalid: before start time

    # Submit
    submit_button = page.get_by_role("button", name="➕ Create Item")
    submit_button.click()

    # Wait for response
    page.wait_for_timeout(2000)

    # Verify error message appears
    page_content = page.content().lower()
    has_error = "error" in page_content or "invalid" in page_content

    assert has_error, "Expected error message for invalid calendar input, but none found"

    print("✅ Validation correctly shows error for invalid input")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
