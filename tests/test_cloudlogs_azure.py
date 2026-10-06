from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gsa_compliance_robot.cloudlogs.azure import AzureMonitorClient


class TestRunQueryAndWait:
    def test_raises_import_error_with_helpful_message_when_sdk_missing(self):
        client = AzureMonitorClient()
        with patch.dict("sys.modules", {"azure.identity": None, "azure.monitor.query": None}):
            with pytest.raises(ImportError, match="azure-monitor-query and azure-identity"):
                client.run_query_and_wait("workspace-1", "SomeTable | take 10")

    @patch("azure.monitor.query.LogsQueryClient")
    @patch("azure.identity.DefaultAzureCredential")
    def test_returns_results_as_list_of_dicts(self, mock_cred, mock_client_cls):
        mock_table = MagicMock()
        mock_table.columns = [MagicMock(name="col")]
        mock_table.columns[0].name = "message"
        mock_table.rows = [["hello"], ["world"]]

        mock_response = MagicMock()
        mock_response.tables = [mock_table]

        mock_client = MagicMock()
        mock_client.query_workspace.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = AzureMonitorClient()
        results, meta = client.run_query_and_wait("workspace-1", "SomeTable | take 10")

        assert results == [{"message": "hello"}, {"message": "world"}]
        assert meta["tables"] == [mock_table]

    @patch("azure.monitor.query.LogsQueryClient")
    @patch("azure.identity.DefaultAzureCredential")
    def test_passes_workspace_and_query_through(self, mock_cred, mock_client_cls):
        mock_response = MagicMock()
        mock_response.tables = []
        mock_client = MagicMock()
        mock_client.query_workspace.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = AzureMonitorClient()
        client.run_query_and_wait("my-workspace", "MyTable | take 5")

        mock_client.query_workspace.assert_called_once_with(
            "my-workspace", "MyTable | take 5", timespan=None
        )

    @patch("azure.monitor.query.LogsQueryClient")
    @patch("azure.identity.DefaultAzureCredential")
    def test_handles_malformed_response_tables_gracefully(self, mock_cred, mock_client_cls):
        # response.tables raises AttributeError -> suppressed, results stays empty
        mock_response = MagicMock()
        type(mock_response).tables = property(lambda self: (_ for _ in ()).throw(AttributeError))
        mock_client = MagicMock()
        mock_client.query_workspace.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = AzureMonitorClient()
        results, meta = client.run_query_and_wait("ws", "query")

        assert results == []


class TestStartQuery:
    @patch("azure.monitor.query.LogsQueryClient")
    @patch("azure.identity.DefaultAzureCredential")
    def test_start_query_runs_synchronously(self, mock_cred, mock_client_cls):
        mock_response = MagicMock()
        mock_response.tables = []
        mock_client = MagicMock()
        mock_client.query_workspace.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = AzureMonitorClient()
        results, meta = client.start_query("ws", "query")

        assert results == []
        mock_client.query_workspace.assert_called_once()
