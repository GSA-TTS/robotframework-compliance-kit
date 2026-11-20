from __future__ import annotations

import json
from pathlib import Path

import pytest

from gsa_compliance_robot.browser_recording import (
    BrowserRecording,
    recording_payload,
    wait_for_operator_confirmation,
    write_closed_page_recording,
    write_sanitized_events,
)


def test_write_sanitized_events_removes_sensitive_fields(tmp_path: Path):
    raw_events = [
        {
            "event_type": "change",
            "origin": "https://example.gov",
            "path": "/settings",
            "tag": "input",
            "aria_label": "Group members",
            "value": "sensitive@example.gov",
            "cookies": "sensitive-cookie",
        }
    ]
    path = write_sanitized_events(json.dumps(raw_events), str(tmp_path))
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["event_count"] == 1
    assert data["page_closed"] is False
    assert "value" not in data["events"][0]
    assert "cookies" not in data["events"][0]


def test_closed_page_and_non_list_validation(tmp_path: Path, monkeypatch):
    closed_path = write_closed_page_recording(str(tmp_path))
    data = json.loads(Path(closed_path).read_text(encoding="utf-8"))
    assert data["page_closed"] is True
    assert data["events"] == []

    with pytest.raises(ValueError, match="must be a list"):
        recording_payload({"not": "a list"})

    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    wait_for_operator_confirmation()

    def _eof(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", _eof)
    with pytest.raises(RuntimeError, match="Interactive stdin"):
        BrowserRecording().wait_for_operator_confirmation()
