"""
Playwright Configuration for E2E Tests
=======================================
Shared Playwright configuration for all UI E2E tests.

Usage:
    pytest tests/e2e/test_*.py -v
"""

import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


@pytest.fixture(scope="function")
def page() -> Page:
    """
    Provide a Playwright page for each test.

    Creates a new browser, context, and page for each test function.
    Cleans up after the test completes.

    Yields:
        Page: Playwright page instance
    """
    with sync_playwright() as p:
        # Launch browser (headless=True for CI, False for local debugging)
        browser = p.chromium.launch(headless=True)

        # Create new context with reasonable defaults
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="en-US"
        )

        # Create page
        page = context.new_page()

        # Increase default timeout for Streamlit (which can be slow to render)
        page.set_default_timeout(10000)  # 10 seconds

        yield page

        # Cleanup
        context.close()
        browser.close()


@pytest.fixture(scope="function")
def streamlit_app_url() -> str:
    """
    Return the URL for the Streamlit app.

    Assumes Streamlit is running on localhost:8501 (default port).
    For CI, you may need to start Streamlit before tests.
    """
    return "http://localhost:8501"
