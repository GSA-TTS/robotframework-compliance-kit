from __future__ import annotations

from unittest.mock import MagicMock, patch

from gsa_compliance_robot.browser_session import BrowserSession


def _patched_builtin(browser_lib, variables=None):
    """Build a mock BuiltIn() whose get_library_instance('Browser') returns
    browser_lib, and whose get_variable_value raises for any name not
    present in `variables` (mimicking Robot's real behavior when a suite
    variable doesn't exist yet)."""
    variables = variables or {}
    builtin = MagicMock()
    builtin.get_library_instance.return_value = browser_lib

    def _get_variable_value(name):
        if name in variables:
            return variables[name]
        raise Exception(f"Variable '{name}' not found")

    builtin.get_variable_value.side_effect = _get_variable_value
    return builtin


class TestInitializeBrowserSafely:
    @patch.object(BrowserSession, "_builtin")
    def test_creates_new_browser_when_none_exists(self, mock_builtin_method, monkeypatch):
        monkeypatch.delenv("BROWSER_HEADLESS", raising=False)
        browser_lib = MagicMock()
        browser_lib.get_browser_ids.return_value = []
        browser_lib.new_context.return_value = "ctx-1"
        browser_lib.new_page.return_value = "page-1"
        mock_builtin_method.return_value = _patched_builtin(browser_lib)

        BrowserSession().initialize_browser_safely()

        browser_lib.new_browser.assert_called_once_with("chromium", headless=False)
        browser_lib.new_context.assert_called_once()
        browser_lib.new_page.assert_called_once()

    @patch.object(BrowserSession, "_builtin")
    def test_reuses_existing_browser_and_context_and_page(self, mock_builtin_method):
        browser_lib = MagicMock()
        browser_lib.get_browser_ids.return_value = ["existing-id"]
        mock_builtin_method.return_value = _patched_builtin(
            browser_lib,
            variables={"${BROWSER_CONTEXT}": "ctx-existing", "${PAGE}": "page-existing"},
        )

        BrowserSession().initialize_browser_safely()

        browser_lib.new_browser.assert_not_called()
        browser_lib.new_context.assert_not_called()
        browser_lib.new_page.assert_not_called()

    @patch.object(BrowserSession, "_builtin")
    def test_honours_browser_headless_env_var(self, mock_builtin_method, monkeypatch):
        monkeypatch.setenv("BROWSER_HEADLESS", "true")
        browser_lib = MagicMock()
        browser_lib.get_browser_ids.return_value = []
        mock_builtin_method.return_value = _patched_builtin(browser_lib)

        BrowserSession().initialize_browser_safely()

        browser_lib.new_browser.assert_called_once_with("chromium", headless=True)


class TestCheckBrowserHealth:
    @patch.object(BrowserSession, "_builtin")
    def test_does_nothing_when_browser_alive(self, mock_builtin_method):
        browser_lib = MagicMock()
        browser_lib.get_browser_ids.return_value = ["id-1"]
        mock_builtin_method.return_value = _patched_builtin(browser_lib)

        session = BrowserSession()
        with patch.object(session, "initialize_browser_safely") as mock_init:
            session.check_browser_health()
            mock_init.assert_not_called()

    @patch.object(BrowserSession, "_builtin")
    def test_reinitializes_when_browser_dead(self, mock_builtin_method):
        browser_lib = MagicMock()
        browser_lib.get_browser_ids.side_effect = Exception("no browser")
        mock_builtin_method.return_value = _patched_builtin(browser_lib)

        session = BrowserSession()
        with patch.object(session, "initialize_browser_safely") as mock_init:
            session.check_browser_health()
            mock_init.assert_called_once()


class TestCloseBrowserSafely:
    @patch.object(BrowserSession, "_builtin")
    def test_closes_context_and_browser(self, mock_builtin_method):
        browser_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(
            browser_lib, variables={"${BROWSER_CONTEXT}": "ctx-1"}
        )

        BrowserSession().close_browser_safely()

        browser_lib.close_context.assert_called_once_with("ctx-1")
        browser_lib.close_browser.assert_called_once()

    @patch.object(BrowserSession, "_builtin")
    def test_swallows_errors_when_no_context_variable(self, mock_builtin_method):
        browser_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(browser_lib)

        # Should not raise even though ${BROWSER_CONTEXT} doesn't exist.
        BrowserSession().close_browser_safely()
        browser_lib.close_browser.assert_called_once()

    @patch.object(BrowserSession, "_builtin")
    def test_swallows_errors_from_close_browser(self, mock_builtin_method):
        browser_lib = MagicMock()
        browser_lib.close_browser.side_effect = Exception("already closed")
        mock_builtin_method.return_value = _patched_builtin(browser_lib)

        # Should not raise.
        BrowserSession().close_browser_safely()


class TestTakeScreenshotArtifact:
    @patch.object(BrowserSession, "_builtin")
    def test_without_locator(self, mock_builtin_method):
        browser_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(browser_lib)

        BrowserSession().take_screenshot_artifact("/tmp/shot.png")

        browser_lib.take_screenshot.assert_called_once_with(filename="/tmp/shot.png")

    @patch.object(BrowserSession, "_builtin")
    def test_with_locator(self, mock_builtin_method):
        browser_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(browser_lib)

        BrowserSession().take_screenshot_artifact("/tmp/shot.png", locator="css=.foo")

        browser_lib.take_screenshot.assert_called_once_with(
            filename="/tmp/shot.png", selector="css=.foo"
        )


class TestSaveStorageStateToFile:
    @patch.object(BrowserSession, "_builtin")
    def test_copies_state_file_to_destination(self, mock_builtin_method, tmp_path):
        source_state = tmp_path / "source_state.json"
        source_state.write_text('{"cookies": []}')
        dest = tmp_path / "nested" / "dest_state.json"

        browser_lib = MagicMock()
        browser_lib.save_storage_state.return_value = str(source_state)
        mock_builtin_method.return_value = _patched_builtin(browser_lib)

        BrowserSession().save_storage_state_to_file(str(dest))

        assert dest.is_file()
        assert dest.read_text() == '{"cookies": []}'

    @patch.object(BrowserSession, "_builtin")
    def test_raises_if_copy_fails_silently(self, mock_builtin_method, tmp_path, monkeypatch):
        source_state = tmp_path / "source_state.json"
        source_state.write_text("{}")
        dest = tmp_path / "dest_state.json"

        browser_lib = MagicMock()
        browser_lib.save_storage_state.return_value = str(source_state)
        mock_builtin_method.return_value = _patched_builtin(browser_lib)

        # Simulate the destination never actually being created.
        monkeypatch.setattr("os.path.isfile", lambda _p: False)

        import pytest

        with pytest.raises(RuntimeError, match="Failed to write storage state"):
            BrowserSession().save_storage_state_to_file(str(dest))
