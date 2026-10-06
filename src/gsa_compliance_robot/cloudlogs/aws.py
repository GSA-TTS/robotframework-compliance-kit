"""AWS CloudWatch Logs Insights adapter.

Ported from M-26-14 (lib/aws_insights.py). Behavior preserved exactly
(retry-on-ExpiredToken, polling loop, metadata shape) — only wrapped to
conform to the shared `CloudLogQueryClient` interface.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from .base import CloudLogQueryClient

log = logging.getLogger(__name__)


class AwsInsightsClient(CloudLogQueryClient):
    """CloudWatch Logs Insights query client.

    Example:
        client = AwsInsightsClient(region="us-east-1")
        results, meta = client.run_query_and_wait("my-log-group", "fields @message")
    """

    def __init__(self, region: str = "us-east-1") -> None:
        self.region = region

    def _make_client(self, region: str | None = None):
        import boto3

        return boto3.client("logs", region_name=region or self.region)

    def start_query(
        self,
        log_group: str,
        query: str,
        start_time: int | float | None = None,
        end_time: int | float | None = None,
        region: str | None = None,
    ) -> tuple[str | None, dict[str, Any]]:
        """Start a CloudWatch Logs Insights query; does not poll for results."""
        client = self._make_client(region)
        params: dict[str, Any] = {"logGroupName": log_group, "queryString": query}
        if start_time is not None:
            params["startTime"] = int(start_time)
        if end_time is not None:
            params["endTime"] = int(end_time)

        resp = client.start_query(**params)
        qid = resp.get("queryId")
        return qid, resp

    def run_query_and_wait(
        self,
        log_group: str,
        query: str,
        start_time: int | float | None = None,
        end_time: int | float | None = None,
        timeout: float = 60,
        poll_interval: float = 1,
        region: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Start a query and poll until completion or timeout.

        Retries once on an expired-token error by recreating the boto3
        client (handles short-lived STS credentials expiring mid-poll).
        """
        try:
            import botocore
        except Exception:
            botocore = None  # noqa: N806

        _region = region or self.region
        client = self._make_client(_region)
        params: dict[str, Any] = {"logGroupName": log_group, "queryString": query}
        if start_time is not None:
            params["startTime"] = int(start_time)
        if end_time is not None:
            params["endTime"] = int(end_time)

        def _is_expired_token(exc: Exception) -> bool:
            msg = str(exc)
            if "ExpiredToken" in msg or "ExpiredTokenException" in msg:
                return True
            if botocore is not None:
                try:
                    if isinstance(exc, botocore.exceptions.ClientError):
                        code = exc.response.get("Error", {}).get("Code", "")
                        return "ExpiredToken" in code
                except Exception:  # noqa: BLE001
                    pass
            return False

        resp = None
        for _attempt in range(3):
            try:
                resp = client.start_query(**params)
                break
            except Exception as exc:  # noqa: BLE001
                if _is_expired_token(exc):
                    client = self._make_client(_region)
                    time.sleep(1)
                    continue
                log.error("AwsInsightsClient: failed to start query: %s", exc)
                return [], {
                    "error": str(exc),
                    "status": "Error",
                    "queryId": None,
                    "started": None,
                }
        if resp is None:
            return [], {
                "error": "failed to start query after retries",
                "status": "Error",
                "queryId": None,
                "started": None,
            }

        qid = resp.get("queryId")
        metadata: dict[str, Any] = {"queryId": qid, "started": resp}
        deadline = time.time() + float(timeout)
        last_result = None

        while time.time() < deadline:
            try:
                result = client.get_query_results(queryId=qid)
            except Exception as exc:  # noqa: BLE001
                if _is_expired_token(exc):
                    client = self._make_client(_region)
                    time.sleep(float(poll_interval))
                    continue
                log.error("AwsInsightsClient: get_query_results failed: %s", exc)
                return [], {
                    "error": str(exc),
                    "status": "Error",
                    "queryId": qid,
                    "final": None,
                }

            last_result = result
            status = result.get("status")
            metadata["status"] = status
            if "statistics" in result:
                metadata["statistics"] = result.get("statistics")
                log.info(
                    "AwsInsightsClient: statistics=%s",
                    json.dumps(result.get("statistics")),
                )
            if status == "Complete":
                metadata["final"] = result
                return result.get("results", []), metadata
            time.sleep(float(poll_interval))

        if last_result is None:
            last_result = client.get_query_results(queryId=qid)
        metadata["status"] = last_result.get("status")
        if "statistics" in last_result:
            metadata["statistics"] = last_result.get("statistics")
        metadata["final"] = last_result
        return last_result.get("results", []), metadata
