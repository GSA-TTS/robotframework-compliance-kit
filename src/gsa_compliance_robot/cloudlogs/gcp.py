"""GCP Cloud Logging adapter.

Ported from M-26-14 (lib/gcp_logging.py), conformed to the shared
`CloudLogQueryClient` interface. Behavior preserved: synchronous
`entries().list` call via google-cloud-logging.
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from .base import CloudLogQueryClient


class GcpLoggingClient(CloudLogQueryClient):
    """Cloud Logging (Log Explorer) query client.

    Requires `google-cloud-logging` to be installed.
    """

    def __init__(self, project: str | None = None) -> None:
        self.project = project

    def start_query(
        self, project: str, filter_: str, page_size: int = 100
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """GCP has no async query concept for Logging — this runs synchronously."""
        return self.run_query_and_wait(project, filter_, page_size=page_size)

    def run_query_and_wait(
        self,
        project: str,
        filter_: str,
        timeout: float = 60,
        page_size: int = 100,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Run a Cloud Logging filter query and return (results, metadata).

        `timeout` is accepted for API parity with other providers but unused
        — `list_entries` is a synchronous paginated call.
        """
        try:
            from google.cloud import logging as gcloud_logging
        except Exception as exc:
            raise ImportError(
                "google-cloud-logging is required for GCP log queries. "
                "Install it with `pip install google-cloud-logging`"
            ) from exc

        client = gcloud_logging.Client(project=project or self.project)
        entries_iter = client.list_entries(filter_=filter_, page_size=page_size)

        results: list[dict[str, Any]] = []
        for count, entry in enumerate(entries_iter, start=1):
            data: dict[str, Any] = {
                "timestamp": getattr(entry, "timestamp", None),
                "log_name": getattr(entry, "log_name", None),
                "resource": getattr(entry, "resource", None),
            }
            with suppress(Exception):
                if hasattr(entry, "payload"):
                    payload = entry.payload
                    if isinstance(payload, dict):
                        data["json_payload"] = payload
                    else:
                        data["text_payload"] = str(payload)
            results.append(data)
            if count >= page_size:
                break

        return results, {"count": len(results)}
