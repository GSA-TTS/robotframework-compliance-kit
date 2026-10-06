"""Allure reporting helpers for Robot Framework suites.

Extracted from gsa-pages (tests/resources/allure.resource). These wrap the
`AllureLibrary` Robot keywords with existence checks so suites don't fail
when an expected artifact (screenshot, log, CSV) wasn't produced.
"""

from __future__ import annotations

import os

__all__ = ["AllureHelpers"]


class AllureHelpers:
    """Robot Framework library: safe Allure attachment keywords.

    Usage in Robot:
        Library    AllureLibrary
        Library    gsa_compliance_robot.allure_helpers.AllureHelpers

        Allure Attach File If Exists    ${path}    name=screenshot
    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def _builtin(self):
        from robot.libraries.BuiltIn import BuiltIn

        return BuiltIn()

    def allure_attach_file_if_exists(
        self, path: str, name: str | None = None, attachment_type: str = "TEXT"
    ) -> None:
        """Attach a file to the current Allure test result only if it exists."""
        if not os.path.isfile(path):
            self._builtin().log(
                f"Allure attachment skipped \u2014 file not found: {path}", "WARN"
            )
            return
        attach_name = name or os.path.basename(path)
        allure_lib = self._builtin().get_library_instance("AllureLibrary")
        allure_lib.attach_file(path, name=attach_name, attachment_type=attachment_type)

    def allure_attach_text_if_exists(self, path: str, name: str | None = None) -> None:
        self.allure_attach_file_if_exists(path, name=name, attachment_type="TEXT")

    def allure_attach_json_if_exists(self, path: str, name: str | None = None) -> None:
        self.allure_attach_file_if_exists(path, name=name, attachment_type="JSON")

    def allure_attach_csv_if_exists(self, path: str, name: str | None = None) -> None:
        self.allure_attach_file_if_exists(path, name=name, attachment_type="CSV")

    def allure_attach_markdown_if_exists(
        self, path: str, name: str | None = None
    ) -> None:
        self.allure_attach_file_if_exists(path, name=name, attachment_type="TEXT")

    def allure_attach_html_if_exists(self, path: str, name: str | None = None) -> None:
        self.allure_attach_file_if_exists(path, name=name, attachment_type="HTML")

    def allure_attach_string_as_text(self, content: str, name: str = "output") -> None:
        """Attach an in-memory string as a text attachment."""
        allure_lib = self._builtin().get_library_instance("AllureLibrary")
        allure_lib.attach(content, name=name, attachment_type="TEXT")
