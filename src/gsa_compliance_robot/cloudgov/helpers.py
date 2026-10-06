"""Cloud.gov audit-event and CSV-export helpers.

Ported from M-26-14 (lib/CloudGovHelpers.py). Pure data transforms, no
network calls, kept separate from `client.py` so they're trivially unit
testable without mocking HTTP.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from io import StringIO
from typing import Any

__all__ = ["convert_json_events_to_csv", "filter_events_by_date_range"]


def convert_json_events_to_csv(events_json: str | dict[str, Any]) -> str:
    """Convert a cloud.gov `/v3/audit_events` JSON payload to CSV text.

    Columns: Timestamp, Actor, Event Type, Target, App GUID, Service GUID.
    """
    events_data = json.loads(events_json) if isinstance(events_json, str) else events_json

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Timestamp", "Actor", "Event Type", "Target", "App GUID", "Service GUID"]
    )
    for resource in events_data.get("resources", []):
        entity = resource.get("entity", {})
        metadata = entity.get("metadata", {})
        request = metadata.get("request", {})
        writer.writerow(
            [
                entity.get("timestamp", ""),
                entity.get("actor_username", ""),
                entity.get("type", ""),
                entity.get("actee_name", ""),
                request.get("app_guid", ""),
                request.get("service_instance_guid", ""),
            ]
        )
    return output.getvalue()


def filter_events_by_date_range(
    events_json: str | dict[str, Any], start_date: str, end_date: str
) -> dict[str, Any]:
    """Return a copy of `events_json` with `resources` filtered to [start_date, end_date].

    Dates are ISO 8601 strings (`Z` suffix accepted).

    .. note::
        **Behavior change from the original M-26-14 implementation**: the
        source ``CloudGovHelpers.filter_events_by_date_range`` mutated its
        input dict in place when a dict (rather than a JSON string) was
        passed — ``events_data["resources"] = filtered`` on the *same
        object* the caller passed in. This version always returns a new
        dict via a shallow copy (``dict(events_json)``), so callers holding
        a reference to the original dict will **not** see it mutated. This
        is deliberate: implicit mutation of caller-owned data is a common
        source of hard-to-trace bugs, and no consumer of the original
        function has migrated to this package yet (see
        https://github.com/GSA-TTS/robotframework-compliance-kit/issues/9),
        so there is no compatibility constraint preventing the safer
        behavior. If M-26-14 migrates (issue #11) and happens to depend on
        the old mutate-in-place behavior, that dependency should be fixed
        at the call site, not reintroduced here.
    """
    events_data = json.loads(events_json) if isinstance(events_json, str) else dict(events_json)

    start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    filtered = []
    for resource in events_data.get("resources", []):
        event_time = resource.get("entity", {}).get("timestamp", "")
        if not event_time:
            continue
        event_dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
        if start_dt <= event_dt <= end_dt:
            filtered.append(resource)

    events_data["resources"] = filtered
    return events_data
