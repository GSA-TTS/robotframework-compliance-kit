"""Playwright/Browser (rf-browser) session lifecycle helpers.

Extracted from gsa-pages (tests/resources/browser.resource), which was
already the canonical implementation inside that repo (common.resource
intentionally left Browser-library keywords unimplemented so pure-API
suites didn't trigger the rfbrowser listener).

These are plain Python functions wrapping the `Browser` library's Robot
keywords via `robot.libraries.BuiltIn`, so they're callable both from Robot
(as library keywords, since this module can be imported with
`Library    gsa_compliance_robot.browser_session.BrowserSession`) and from
plain Python test code if needed.
"""

from __future__ import annotations

import os

__all__ = ["BrowserSession"]


class BrowserSession:
    """Robot Framework library providing safe Browser (Playwright) lifecycle keywords.

    Honors the `BROWSER_HEADLESS` environment variable (default: false)
    for all `New Browser` calls, and reuses an existing browser/context/page
    when one is already active in the current suite — avoiding the "second
    browser leaks the first" failure mode that motivated this helper in the
    source repo.

    Usage in Robot:
        Library    gsa_compliance_robot.browser_session.BrowserSession
        Library    Browser

        Initialize Browser Safely
        ...
        Close Browser Safely
    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def _builtin(self):
        from robot.libraries.BuiltIn import BuiltIn

        return BuiltIn()

    def initialize_browser_safely(self) -> None:
        """Initialize browser, context, and page with proper error handling.

        Reuses an existing browser/context/page when available; honours the
        `BROWSER_HEADLESS` env var (default: false for local dev, set to
        `true` in CI).
        """
        builtin = self._builtin()
        browser_lib = builtin.get_library_instance("Browser")

        existing_ids = browser_lib.get_browser_ids()
        headless = os.environ.get("BROWSER_HEADLESS", "false").lower() == "true"

        if not existing_ids:
            browser_lib.new_browser("chromium", headless=headless)

        try:
            builtin.get_variable_value("${BROWSER_CONTEXT}")
            has_context = True
        except Exception:  # noqa: BLE001
            has_context = False
        if not has_context:
            context = browser_lib.new_context()
            builtin.set_suite_variable("${BROWSER_CONTEXT}", context)

        try:
            builtin.get_variable_value("${PAGE}")
            has_page = True
        except Exception:  # noqa: BLE001
            has_page = False
        if not has_page:
            page = browser_lib.new_page()
            builtin.set_suite_variable("${PAGE}", page)

    def check_browser_health(self) -> None:
        """Check if the browser is alive; reinitialize if not."""
        builtin = self._builtin()
        browser_lib = builtin.get_library_instance("Browser")
        try:
            browser_lib.get_browser_ids()
        except Exception:  # noqa: BLE001
            self.initialize_browser_safely()

    def close_browser_safely(self) -> None:
        """Close the browser context and all browsers, swallowing errors."""
        builtin = self._builtin()
        browser_lib = builtin.get_library_instance("Browser")
        try:
            context = builtin.get_variable_value("${BROWSER_CONTEXT}")
            browser_lib.close_context(context)
        except Exception:  # noqa: BLE001
            pass
        try:
            browser_lib.close_browser()
        except Exception:  # noqa: BLE001
            pass

    def take_screenshot_artifact(
        self, filepath: str, locator: str | None = None
    ) -> None:
        """Take a screenshot and save it to `filepath` (caller supplies full path)."""
        builtin = self._builtin()
        browser_lib = builtin.get_library_instance("Browser")
        if locator:
            browser_lib.take_screenshot(filename=filepath, selector=locator)
        else:
            browser_lib.take_screenshot(filename=filepath)

    def save_storage_state_to_file(self, filepath: str) -> None:
        """Save the current browser context's storage state (cookies, localStorage) to `filepath`."""
        import shutil

        builtin = self._builtin()
        browser_lib = builtin.get_library_instance("Browser")
        state_file = browser_lib.save_storage_state()
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        shutil.copyfile(state_file, filepath)
        if not os.path.isfile(filepath):
            raise RuntimeError(f"Failed to write storage state to {filepath}")
