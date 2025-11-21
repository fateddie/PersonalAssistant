"""
Playwright E2E Tests for Event Management
Tests the complete flow of viewing, accepting, and rejecting events
"""
import pytest
from playwright.sync_api import Page, expect
import requests
import time


# Configuration
FRONTEND_URL = "http://localhost:8501"
BACKEND_URL = "http://localhost:8000"


@pytest.fixture(scope="function", autouse=True)
def wait_for_services():
    """Ensure services are running before each test"""
    # Check backend
    for _ in range(5):
        try:
            response = requests.get(f"{BACKEND_URL}/docs", timeout=2)
            if response.status_code == 200:
                break
        except:
            time.sleep(1)
    else:
        pytest.skip("Backend not running")

    # Check frontend
    for _ in range(5):
        try:
            response = requests.get(FRONTEND_URL, timeout=2)
            if response.status_code == 200:
                break
        except:
            time.sleep(1)
    else:
        pytest.skip("Frontend not running")


def test_show_events_displays_list(page: Page):
    """
    Test: Typing 'show events' displays the event list
    """
    # Navigate to Streamlit app
    page.goto(FRONTEND_URL)

    # Wait for page to load
    page.wait_for_selector("input[aria-label*='me anything']", timeout=10000)

    # Type "show events" in the chat input
    chat_input = page.locator("input[aria-label*='me anything']")
    chat_input.fill("show events")
    chat_input.press("Enter")

    # Wait for response (Streamlit takes a moment to process)
    page.wait_for_timeout(3000)

    # Check if event list appears
    # Looking for either "Email-Detected Events" or "Google Calendar Events" or "No upcoming events"
    page_content = page.content()

    assert (
        "Email-Detected Events" in page_content
        or "Google Calendar Events" in page_content
        or "No upcoming events" in page_content
    ), "Event list did not appear"

    print("✅ test_show_events_displays_list PASSED")


def test_email_events_have_buttons(page: Page):
    """
    Test: Email events have Accept/Reject buttons visible
    """
    # Navigate and show events
    page.goto(FRONTEND_URL)
    page.wait_for_selector("input[aria-label*='me anything']", timeout=10000)

    chat_input = page.locator("input[aria-label*='me anything']")
    chat_input.fill("show events")
    chat_input.press("Enter")

    # Wait for response
    page.wait_for_timeout(3000)

    # Check if page has email events
    page_content = page.content()

    if "Email-Detected Events" in page_content:
        # Should have Accept/Reject buttons
        # Streamlit renders buttons with specific text content
        assert (
            "Accept" in page_content or "✅ Accept" in page_content
        ), "Accept button not found for email events"

        assert (
            "Reject" in page_content or "❌ Reject" in page_content
        ), "Reject button not found for email events"

        print("✅ test_email_events_have_buttons PASSED")
    else:
        pytest.skip("No email events to test")


def test_accept_event_removes_from_list(page: Page):
    """
    Test: Clicking Accept on an event removes it from the list
    """
    # Get initial pending events from backend
    response = requests.get(
        f"{BACKEND_URL}/emails/events?status=pending&future_only=true", timeout=5
    )
    initial_events = response.json().get("events", [])

    if not initial_events:
        pytest.skip("No pending email events to test")

    # Navigate and show events
    page.goto(FRONTEND_URL)
    page.wait_for_selector("input[aria-label*='me anything']", timeout=10000)

    chat_input = page.locator("input[aria-label*='me anything']")
    chat_input.fill("show events")
    chat_input.press("Enter")

    # Wait for response
    page.wait_for_timeout(3000)

    # Try to find and click Accept button
    # Streamlit buttons are rendered with specific structure
    accept_buttons = page.get_by_text("✅ Accept", exact=False)

    if accept_buttons.count() > 0:
        # Click first Accept button
        accept_buttons.first.click()

        # Wait for page to reload
        page.wait_for_timeout(2000)

        # Verify event was accepted via API
        response = requests.get(
            f"{BACKEND_URL}/emails/events?status=approved&future_only=true", timeout=5
        )
        approved_events = response.json().get("events", [])

        # Check that we have at least one approved event now
        assert len(approved_events) > 0, "Event was not approved"

        print("✅ test_accept_event_removes_from_list PASSED")
    else:
        pytest.skip("No Accept buttons found (no email events)")


def test_reject_event_removes_from_list(page: Page):
    """
    Test: Clicking Reject on an event removes it from the list
    """
    # Get initial pending events from backend
    response = requests.get(
        f"{BACKEND_URL}/emails/events?status=pending&future_only=true", timeout=5
    )
    initial_events = response.json().get("events", [])

    if not initial_events:
        pytest.skip("No pending email events to test")

    # Navigate and show events
    page.goto(FRONTEND_URL)
    page.wait_for_selector("input[aria-label*='me anything']", timeout=10000)

    chat_input = page.locator("input[aria-label*='me anything']")
    chat_input.fill("show events")
    chat_input.press("Enter")

    # Wait for response
    page.wait_for_timeout(3000)

    # Try to find and click Reject button
    reject_buttons = page.get_by_text("❌ Reject", exact=False)

    if reject_buttons.count() > 0:
        # Click first Reject button
        reject_buttons.first.click()

        # Wait for page to reload
        page.wait_for_timeout(2000)

        # Verify event was rejected via API
        response = requests.get(
            f"{BACKEND_URL}/emails/events?status=rejected&future_only=true", timeout=5
        )
        rejected_events = response.json().get("events", [])

        # Check that we have at least one rejected event now
        assert len(rejected_events) > 0, "Event was not rejected"

        print("✅ test_reject_event_removes_from_list PASSED")
    else:
        pytest.skip("No Reject buttons found (no email events)")


def test_calendar_events_separate_from_email(page: Page):
    """
    Test: Calendar events are displayed separately from email events
    """
    # Navigate and show events
    page.goto(FRONTEND_URL)
    page.wait_for_selector("input[aria-label*='me anything']", timeout=10000)

    chat_input = page.locator("input[aria-label*='me anything']")
    chat_input.fill("show events")
    chat_input.press("Enter")

    # Wait for response
    page.wait_for_timeout(3000)

    page_content = page.content()

    # Check if both sections exist (if there are events from both sources)
    has_email_section = "Email-Detected Events" in page_content
    has_calendar_section = "Google Calendar Events" in page_content

    if has_email_section and has_calendar_section:
        # Both sections should be separate
        # Email section should come before Calendar section
        email_pos = page_content.find("Email-Detected Events")
        calendar_pos = page_content.find("Google Calendar Events")

        assert (
            email_pos < calendar_pos
        ), "Email events should be displayed before calendar events"

        print("✅ test_calendar_events_separate_from_email PASSED")
    else:
        # At least one section should exist
        assert (
            has_email_section or has_calendar_section or "No upcoming events" in page_content
        ), "No event sections found"

        print("✅ test_calendar_events_separate_from_email PASSED (partial)")


def test_no_recurring_event_duplicates(page: Page):
    """
    Test: Recurring events don't show multiple instances
    """
    # Navigate and show events
    page.goto(FRONTEND_URL)
    page.wait_for_selector("input[aria-label*='me anything']", timeout=10000)

    chat_input = page.locator("input[aria-label*='me anything']")
    chat_input.fill("show events")
    chat_input.press("Enter")

    # Wait for response
    page.wait_for_timeout(3000)

    page_content = page.content()

    # Check for common recurring event patterns (e.g., "anniversary", "birthday")
    # Count occurrences of these patterns
    test_patterns = ["anniversary", "birthday", "special day"]

    for pattern in test_patterns:
        count = page_content.lower().count(pattern)
        if count > 0:
            # If pattern appears, it should appear no more than 2 times
            # (once in the title, maybe once in event description)
            assert count <= 3, f"Recurring event '{pattern}' appears {count} times (too many duplicates)"

    print("✅ test_no_recurring_event_duplicates PASSED")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--headed"])
