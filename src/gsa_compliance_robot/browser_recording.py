"""Sanitized artifact helpers for interactive RF Browser exploration.

Extracted from gsa-pages (scripts/testing/browser_recording.py +
tests/resources/browser_recording.resource). Records only allowlisted DOM
event metadata (`timestamp`, `event_type`, `origin`, `path`, `tag`, `role`,
`aria_label`, `name`, `disabled`) and never persists input values, cookies,
or browser storage.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = [
    "ACTION_RECORDER_JS",
    "SAFE_FIELDS",
    "BrowserRecording",
    "get_recorder_script",
    "recording_payload",
    "wait_for_operator_confirmation",
    "write_closed_page_recording",
    "write_sanitized_events",
]

ACTION_RECORDER_JS = """() => {
  window.__gsaPagesActions = [];
  const metadata = target => ({
    timestamp: new Date().toISOString(),
    origin: window.location.origin,
    path: window.location.pathname,
    tag: target.tagName.toLowerCase(),
    role: target.getAttribute('role') || '',
    aria_label: target.getAttribute('aria-label') || '',
    name: target.getAttribute('name') || '',
    disabled: Boolean(target.disabled || target.getAttribute('aria-disabled') === 'true')
  });
  for (const eventType of ['click', 'focus', 'change']) {
    document.addEventListener(eventType, event => {
      window.__gsaPagesActions.push({event_type: eventType, ...metadata(event.target)});
    }, true);
  }
}"""

SAFE_FIELDS = {
    "timestamp",
    "event_type",
    "origin",
    "path",
    "tag",
    "role",
    "aria_label",
    "name",
    "disabled",
}


def recording_payload(events: Any, page_closed: bool = False) -> dict[str, Any]:
    """Build a redacted artifact even when an operator closes the target page."""
    if not isinstance(events, list):
        raise ValueError("Browser recording events must be a list")
    sanitized = [
        {key: event[key] for key in SAFE_FIELDS & event.keys()}
        for event in events
        if isinstance(event, dict)
    ]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "event_count": len(sanitized),
        "page_closed": page_closed,
        "events": sanitized,
    }


class BrowserRecording:
    """Robot Framework library for operator-confirmed, redacted recordings."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def wait_for_operator_confirmation(self) -> None:
        try:
            input(
                "Perform the browser steps, then press Enter here to save sanitized metadata: "
            )
        except EOFError as error:
            raise RuntimeError(
                "Interactive stdin is unavailable; run task rf:browser-record from a terminal."
            ) from error

    def write_sanitized_events(self, events: Any, record_dir: str) -> str:
        """Write only allowlisted metadata; never persist input values or session state."""
        if isinstance(events, str):
            events = json.loads(events)
        output_dir = Path(record_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "sanitized-actions.json"
        output_path.write_text(
            json.dumps(recording_payload(events), indent=2) + "\n",
            encoding="utf-8",
        )
        return str(output_path)

    def write_closed_page_recording(self, record_dir: str) -> str:
        """Write a safe empty result when the target page is no longer open."""
        output_dir = Path(record_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "sanitized-actions.json"
        output_path.write_text(
            json.dumps(recording_payload([], page_closed=True), indent=2) + "\n",
            encoding="utf-8",
        )
        return str(output_path)


_RECORDER = BrowserRecording()


def get_recorder_script() -> str:
    """Return the browser JavaScript expression that installs DOM action listeners."""
    return ACTION_RECORDER_JS


def wait_for_operator_confirmation() -> None:
    """Expose the confirmation prompt as a Robot Framework module keyword."""
    _RECORDER.wait_for_operator_confirmation()


def write_sanitized_events(events: Any, record_dir: str) -> str:
    """Expose redacted artifact writing as a Robot Framework module keyword."""
    return _RECORDER.write_sanitized_events(events, record_dir)


def write_closed_page_recording(record_dir: str) -> str:
    """Expose closed-page artifact writing as a Robot Framework keyword."""
    return _RECORDER.write_closed_page_recording(record_dir)
