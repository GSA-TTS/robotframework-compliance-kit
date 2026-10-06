"""Abstract base for cloud log-query clients.

Extracted from the repeated pattern in M-26-14's resources/{azure,gcp}_common.resource
and resources/common.resource (AWS): each provider shim implemented the same
"start query" / "run query and wait" shape against a different SDK. This
module defines one interface so new providers can be added consistently and
Robot keywords can be written once against the ABC rather than per-provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["CloudLogQueryClient"]


class CloudLogQueryClient(ABC):
    """Common interface for provider-specific log/insights query clients.

    Implementations: `gsa_compliance_robot.cloudlogs.aws.AwsInsightsClient`,
    `.azure.AzureMonitorClient`, `.gcp.GcpLoggingClient`.
    """

    @abstractmethod
    def start_query(self, *args: Any, **kwargs: Any) -> tuple[Any, dict[str, Any]]:
        """Start a query without waiting for completion.

        Returns (query_id_or_None, metadata_dict). For providers without an
        async query concept (Azure, GCP today), this may execute
        synchronously and return results immediately in `metadata`.
        """
        raise NotImplementedError

    @abstractmethod
    def run_query_and_wait(
        self, *args: Any, **kwargs: Any
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Start a query and poll/wait until it completes.

        Returns (results, metadata) where `results` is a list of row dicts
        and `metadata` includes at minimum a `status` key.
        """
        raise NotImplementedError
