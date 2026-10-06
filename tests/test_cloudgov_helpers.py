from __future__ import annotations

import json

import pytest

from gsa_compliance_robot.cloudgov import helpers


SAMPLE_EVENTS = {
    "resources": [
        {
            "entity": {
                "timestamp": "2024-01-15T10:30:00Z",
                "actor_username": "alice@example.gov",
                "type": "audit.service.create",
                "actee_name": "my-service",
                "metadata": {
                    "request": {
                        "app_guid": "app-123",
                        "service_instance_guid": "svc-456",
                    }
                },
            }
        },
        {
            "entity": {
                "timestamp": "2024-02-01T00:00:00Z",
                "actor_username": "bob@example.gov",
                "type": "audit.user.space_developer_add",
                "actee_name": "bob@example.gov",
                "metadata": {"request": {}},
            }
        },
    ]
}


class TestConvertJsonEventsToCsv:
    def test_converts_dict_input(self):
        csv_text = helpers.convert_json_events_to_csv(SAMPLE_EVENTS)
        assert "Timestamp,Actor,Event Type,Target,App GUID,Service GUID" in csv_text
        assert "alice@example.gov" in csv_text
        assert "app-123" in csv_text
        assert "svc-456" in csv_text

    def test_converts_string_input(self):
        csv_text = helpers.convert_json_events_to_csv(json.dumps(SAMPLE_EVENTS))
        assert "alice@example.gov" in csv_text

    def test_handles_missing_metadata(self):
        csv_text = helpers.convert_json_events_to_csv(SAMPLE_EVENTS)
        assert "bob@example.gov" in csv_text

    def test_empty_resources(self):
        csv_text = helpers.convert_json_events_to_csv({"resources": []})
        lines = csv_text.strip().splitlines()
        assert len(lines) == 1  # header only


class TestFilterEventsByDateRange:
    def test_filters_within_range(self):
        filtered = helpers.filter_events_by_date_range(
            SAMPLE_EVENTS, "2024-01-01T00:00:00Z", "2024-01-31T23:59:59Z"
        )
        assert len(filtered["resources"]) == 1
        assert filtered["resources"][0]["entity"]["actor_username"] == "alice@example.gov"

    def test_filters_all_out_of_range(self):
        filtered = helpers.filter_events_by_date_range(
            SAMPLE_EVENTS, "2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z"
        )
        assert filtered["resources"] == []

    def test_accepts_string_input(self):
        filtered = helpers.filter_events_by_date_range(
            json.dumps(SAMPLE_EVENTS), "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"
        )
        assert len(filtered["resources"]) == 2

    def test_skips_entries_without_timestamp(self):
        events = {"resources": [{"entity": {"actor_username": "no-ts"}}]}
        filtered = helpers.filter_events_by_date_range(
            events, "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"
        )
        assert filtered["resources"] == []
