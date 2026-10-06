from __future__ import annotations

from unittest.mock import MagicMock, patch

from gsa_compliance_robot.allure_helpers import AllureHelpers


def _patched_builtin(allure_lib):
    builtin = MagicMock()
    builtin.get_library_instance.return_value = allure_lib
    return builtin


class TestAllureAttachFileIfExists:
    @patch.object(AllureHelpers, "_builtin")
    def test_attaches_when_file_exists(self, mock_builtin_method, tmp_path):
        allure_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(allure_lib)

        f = tmp_path / "evidence.txt"
        f.write_text("content")

        AllureHelpers().allure_attach_file_if_exists(str(f))

        allure_lib.attach_file.assert_called_once_with(
            str(f), name="evidence.txt", attachment_type="TEXT"
        )

    @patch.object(AllureHelpers, "_builtin")
    def test_uses_custom_name(self, mock_builtin_method, tmp_path):
        allure_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(allure_lib)

        f = tmp_path / "evidence.txt"
        f.write_text("content")

        AllureHelpers().allure_attach_file_if_exists(str(f), name="custom-name")

        allure_lib.attach_file.assert_called_once_with(
            str(f), name="custom-name", attachment_type="TEXT"
        )

    @patch.object(AllureHelpers, "_builtin")
    def test_skips_when_file_missing(self, mock_builtin_method, tmp_path):
        allure_lib = MagicMock()
        builtin = _patched_builtin(allure_lib)
        mock_builtin_method.return_value = builtin

        AllureHelpers().allure_attach_file_if_exists(str(tmp_path / "missing.txt"))

        allure_lib.attach_file.assert_not_called()
        builtin.log.assert_called_once()
        assert "not found" in builtin.log.call_args[0][0]

    @patch.object(AllureHelpers, "_builtin")
    def test_custom_attachment_type(self, mock_builtin_method, tmp_path):
        allure_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(allure_lib)

        f = tmp_path / "data.json"
        f.write_text("{}")

        AllureHelpers().allure_attach_file_if_exists(str(f), attachment_type="JSON")

        allure_lib.attach_file.assert_called_once_with(
            str(f), name="data.json", attachment_type="JSON"
        )


class TestTypedAttachmentWrappers:
    @patch.object(AllureHelpers, "_builtin")
    def test_attach_text_if_exists(self, mock_builtin_method, tmp_path):
        allure_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(allure_lib)
        f = tmp_path / "a.txt"
        f.write_text("x")

        AllureHelpers().allure_attach_text_if_exists(str(f))

        _, kwargs = allure_lib.attach_file.call_args
        assert kwargs["attachment_type"] == "TEXT"

    @patch.object(AllureHelpers, "_builtin")
    def test_attach_json_if_exists(self, mock_builtin_method, tmp_path):
        allure_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(allure_lib)
        f = tmp_path / "a.json"
        f.write_text("{}")

        AllureHelpers().allure_attach_json_if_exists(str(f))

        _, kwargs = allure_lib.attach_file.call_args
        assert kwargs["attachment_type"] == "JSON"

    @patch.object(AllureHelpers, "_builtin")
    def test_attach_csv_if_exists(self, mock_builtin_method, tmp_path):
        allure_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(allure_lib)
        f = tmp_path / "a.csv"
        f.write_text("a,b")

        AllureHelpers().allure_attach_csv_if_exists(str(f))

        _, kwargs = allure_lib.attach_file.call_args
        assert kwargs["attachment_type"] == "CSV"

    @patch.object(AllureHelpers, "_builtin")
    def test_attach_markdown_if_exists_uses_text_type(self, mock_builtin_method, tmp_path):
        allure_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(allure_lib)
        f = tmp_path / "a.md"
        f.write_text("# heading")

        AllureHelpers().allure_attach_markdown_if_exists(str(f))

        _, kwargs = allure_lib.attach_file.call_args
        assert kwargs["attachment_type"] == "TEXT"

    @patch.object(AllureHelpers, "_builtin")
    def test_attach_html_if_exists(self, mock_builtin_method, tmp_path):
        allure_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(allure_lib)
        f = tmp_path / "a.html"
        f.write_text("<html></html>")

        AllureHelpers().allure_attach_html_if_exists(str(f))

        _, kwargs = allure_lib.attach_file.call_args
        assert kwargs["attachment_type"] == "HTML"


class TestAllureAttachStringAsText:
    @patch.object(AllureHelpers, "_builtin")
    def test_attaches_in_memory_string(self, mock_builtin_method):
        allure_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(allure_lib)

        AllureHelpers().allure_attach_string_as_text("hello world", name="my-output")

        allure_lib.attach.assert_called_once_with(
            "hello world", name="my-output", attachment_type="TEXT"
        )

    @patch.object(AllureHelpers, "_builtin")
    def test_default_name(self, mock_builtin_method):
        allure_lib = MagicMock()
        mock_builtin_method.return_value = _patched_builtin(allure_lib)

        AllureHelpers().allure_attach_string_as_text("hello world")

        allure_lib.attach.assert_called_once_with(
            "hello world", name="output", attachment_type="TEXT"
        )
