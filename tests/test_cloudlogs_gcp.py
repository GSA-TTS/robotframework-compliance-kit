from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gsa_compliance_robot.cloudlogs.gcp import GcpLoggingClient


class TestRunQueryAndWait:
    def test_raises_import_error_with_helpful_message_when_sdk_missing(self):
        client = GcpLoggingClient()
        with patch.dict("sys.modules", {"google.cloud.logging": None, "google.cloud": None}):
            with pytest.raises(ImportError, match="google-cloud-logging"):
                client.run_query_and_wait("my-project", 'resource.type="gce_instance"')

    @patch("google.cloud.logging.Client")
    def test_returns_entries_as_list_of_dicts(self, mock_client_cls):
        entry1 = MagicMock(timestamp="2024-01-01T00:00:00Z", log_name="log1", resource="res1")
        entry1.payload = {"message": "hello"}
        entry2 = MagicMock(timestamp="2024-01-02T00:00:00Z", log_name="log2", resource="res2")
        entry2.payload = "plain text payload"

        mock_client = MagicMock()
        mock_client.list_entries.return_value = [entry1, entry2]
        mock_client_cls.return_value = mock_client

        client = GcpLoggingClient()
        results, meta = client.run_query_and_wait("my-project", 'resource.type="gce_instance"')

        assert len(results) == 2
        assert results[0]["json_payload"] == {"message": "hello"}
        assert results[1]["text_payload"] == "plain text payload"
        assert meta["count"] == 2

    @patch("google.cloud.logging.Client")
    def test_respects_page_size_limit(self, mock_client_cls):
        entries = [MagicMock(payload=None) for _ in range(10)]
        mock_client = MagicMock()
        mock_client.list_entries.return_value = iter(entries)
        mock_client_cls.return_value = mock_client

        client = GcpLoggingClient()
        results, meta = client.run_query_and_wait("my-project", "filter", page_size=3)

        assert len(results) == 3
        assert meta["count"] == 3

    @patch("google.cloud.logging.Client")
    def test_uses_project_fallback_from_constructor(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.list_entries.return_value = []
        mock_client_cls.return_value = mock_client

        client = GcpLoggingClient(project="default-project")
        client.run_query_and_wait(project=None, filter_="filter")

        mock_client_cls.assert_called_once_with(project="default-project")

    @patch("google.cloud.logging.Client")
    def test_entry_without_payload_attribute(self, mock_client_cls):
        entry = MagicMock(spec=["timestamp", "log_name", "resource"])
        entry.timestamp = "ts"
        entry.log_name = "ln"
        entry.resource = "r"

        mock_client = MagicMock()
        mock_client.list_entries.return_value = [entry]
        mock_client_cls.return_value = mock_client

        client = GcpLoggingClient()
        results, _meta = client.run_query_and_wait("project", "filter")

        assert "json_payload" not in results[0]
        assert "text_payload" not in results[0]


class TestStartQuery:
    @patch("google.cloud.logging.Client")
    def test_start_query_runs_synchronously(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.list_entries.return_value = []
        mock_client_cls.return_value = mock_client

        client = GcpLoggingClient()
        results, meta = client.start_query("my-project", "filter")

        assert results == []
        assert meta["count"] == 0
