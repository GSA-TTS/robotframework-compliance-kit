from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gsa_compliance_robot.cloudlogs.aws import AwsInsightsClient


class TestStartQuery:
    @patch("boto3.client")
    def test_returns_query_id_and_response(self, mock_boto_client):
        mock_client = MagicMock()
        mock_client.start_query.return_value = {"queryId": "qid-123"}
        mock_boto_client.return_value = mock_client

        client = AwsInsightsClient(region="us-east-1")
        qid, resp = client.start_query("my-log-group", "fields @message")
        assert qid == "qid-123"
        assert resp == {"queryId": "qid-123"}

    @patch("boto3.client")
    def test_includes_time_window_when_provided(self, mock_boto_client):
        mock_client = MagicMock()
        mock_client.start_query.return_value = {"queryId": "qid-1"}
        mock_boto_client.return_value = mock_client

        client = AwsInsightsClient()
        client.start_query("lg", "query", start_time=100, end_time=200)
        _, kwargs = mock_client.start_query.call_args
        assert kwargs["startTime"] == 100
        assert kwargs["endTime"] == 200


class TestRunQueryAndWait:
    @patch("time.sleep", lambda *_a, **_k: None)
    @patch("boto3.client")
    def test_returns_results_on_complete(self, mock_boto_client):
        mock_client = MagicMock()
        mock_client.start_query.return_value = {"queryId": "qid-1"}
        mock_client.get_query_results.return_value = {
            "status": "Complete",
            "results": [[{"field": "@message", "value": "hello"}]],
        }
        mock_boto_client.return_value = mock_client

        client = AwsInsightsClient()
        results, meta = client.run_query_and_wait("lg", "query", timeout=5)
        assert results == [[{"field": "@message", "value": "hello"}]]
        assert meta["status"] == "Complete"
        assert meta["queryId"] == "qid-1"

    @patch("boto3.client")
    def test_start_query_failure_returns_error_metadata(self, mock_boto_client):
        mock_client = MagicMock()
        mock_client.start_query.side_effect = Exception("AccessDenied")
        mock_boto_client.return_value = mock_client

        client = AwsInsightsClient()
        results, meta = client.run_query_and_wait("lg", "query", timeout=1)
        assert results == []
        assert meta["status"] == "Error"
        assert "AccessDenied" in meta["error"]

    @patch("time.sleep", lambda *_a, **_k: None)
    @patch("boto3.client")
    def test_retries_on_expired_token(self, mock_boto_client):
        mock_client = MagicMock()
        # First call raises an expired-token-like error, second succeeds.
        mock_client.start_query.side_effect = [
            Exception("ExpiredTokenException: token expired"),
            {"queryId": "qid-retry"},
        ]
        mock_client.get_query_results.return_value = {
            "status": "Complete",
            "results": [],
        }
        mock_boto_client.return_value = mock_client

        client = AwsInsightsClient()
        results, meta = client.run_query_and_wait("lg", "query", timeout=5)
        assert meta["queryId"] == "qid-retry"
        assert results == []
