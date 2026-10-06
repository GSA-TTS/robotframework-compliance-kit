"""Azure Monitor Log Analytics adapter.

Ported from M-26-14 (lib/azure_monitor.py), conformed to the shared
`CloudLogQueryClient` interface. Behavior preserved: synchronous Kusto query
via azure-monitor-query + azure-identity DefaultAzureCredential.
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from .base import CloudLogQueryClient


class AzureMonitorClient(CloudLogQueryClient):
    """Log Analytics query client (Kusto queries, synchronous).

    Requires `azure-monitor-query` and `azure-identity` to be installed.
    """

    def __init__(self, workspace_id: str | None = None) -> None:
        self.workspace_id = workspace_id

    def start_query(
        self, workspace_id: str, query: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Azure Log Analytics has no async query concept — this runs synchronously."""
        return self.run_query_and_wait(workspace_id, query)

    def run_query_and_wait(
        self, workspace_id: str, query: str, timeout: float = 60
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Run a Kusto query against a Log Analytics workspace and return (results, metadata)."""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.monitor.query import LogsQueryClient
        except Exception as exc:
            raise ImportError(
                "azure-monitor-query and azure-identity are required. "
                "Install with `pip install azure-monitor-query azure-identity`"
            ) from exc

        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        response = client.query_workspace(workspace_id, query, timespan=None)

        results: list[dict[str, Any]] = []
        with suppress(Exception):
            for table in response.tables:
                cols = [c.name for c in table.columns]
                for row in table.rows:
                    results.append(dict(zip(cols, row, strict=False)))

        metadata = {"tables": getattr(response, "tables", None)}
        return results, metadata
