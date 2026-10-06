from __future__ import annotations

import json
import os

import pytest

from gsa_compliance_robot import reporting


@pytest.fixture
def store(tmp_path):
    return reporting.ArtifactStore(artifacts_dir=str(tmp_path / "artifacts"))


class TestGenerateArtifactFilename:
    def test_uses_provided_timestamp(self):
        name = reporting.generate_artifact_filename("AC", "evidence", "20240101000000")
        assert name == "AC_evidence_20240101000000"

    def test_generates_timestamp_when_omitted(self):
        name = reporting.generate_artifact_filename("AC", "evidence")
        assert name.startswith("AC_evidence_")
        assert len(name.split("_")[-1]) == 14  # %Y%m%d%H%M%S


class TestArtifactStore:
    def test_creates_directories(self, tmp_path):
        artifacts_dir = tmp_path / "nested" / "artifacts"
        reporting.ArtifactStore(artifacts_dir=str(artifacts_dir))
        assert artifacts_dir.is_dir()

    def test_defaults_reports_dir_to_artifacts_dir(self, tmp_path):
        s = reporting.ArtifactStore(artifacts_dir=str(tmp_path / "a"))
        assert s.reports_dir == s.artifacts_dir

    def test_save_json_roundtrip(self, store):
        path = store.save_json({"key": "value"}, "myfile")
        assert path.endswith("myfile.json")
        with open(path) as f:
            assert json.load(f) == {"key": "value"}

    def test_save_text(self, store):
        path = store.save_text("hello world", "myfile")
        assert path.endswith("myfile.txt")
        assert open(path).read() == "hello world"

    def test_generate_artifact(self, store):
        path = store.generate_artifact("AC-2", "ac2.json")
        data = json.load(open(path))
        assert data["control_id"] == "AC-2"
        assert data["status"] == "generated"


class TestGenerateControlFamilyReport:
    def test_report_contains_expected_fields(self, store):
        report = reporting.generate_control_family_report(
            store, "AC", ["artifact1"], ["finding1"], "Compliant"
        )
        assert report["control_family"] == "AC"
        assert report["artifacts"] == ["artifact1"]
        assert report["findings"] == ["finding1"]
        assert report["compliance_status"] == "Compliant"

    def test_persists_json_and_text(self, store):
        reporting.generate_control_family_report(store, "AC", [], [], "Compliant")
        files = os.listdir(store.artifacts_dir)
        assert any(f.endswith(".json") for f in files)
        assert any(f.endswith(".txt") for f in files)


class TestGenerateExecutiveSummary:
    def test_counts_compliant_families(self, store):
        reports = [
            {"compliance_status": "Compliant", "artifacts": ["a"], "findings": []},
            {"compliance_status": "Generated", "artifacts": ["b", "c"], "findings": []},
            {"compliance_status": "Non-Compliant", "artifacts": [], "findings": ["x"]},
        ]
        summary = reporting.generate_executive_summary(store, reports)
        assert summary["total_families"] == 3
        assert summary["compliant_families"] == 2
        assert summary["total_artifacts"] == 3

    def test_collects_critical_and_high_findings(self, store):
        reports = [
            {
                "compliance_status": "Compliant",
                "artifacts": [],
                "findings": ["CRITICAL: missing control", "informational note"],
            },
            {
                "compliance_status": "Compliant",
                "artifacts": [],
                "findings": ["HIGH: exposed secret"],
            },
        ]
        summary = reporting.generate_executive_summary(store, reports)
        assert len(summary["critical_findings"]) == 2

    def test_zero_families_does_not_divide_by_zero(self, store):
        summary = reporting.generate_executive_summary(store, [])
        assert summary["total_families"] == 0


class TestValidateArtifactCompleteness:
    def test_all_present(self, store):
        result = reporting.validate_artifact_completeness(
            store, "AC", ["AC_evidence_123"], ["AC_evidence"]
        )
        assert result["missing_artifacts"] == []
        assert result["completeness_percentage"] == 100.0

    def test_some_missing(self, store):
        result = reporting.validate_artifact_completeness(
            store, "AC", ["AC_evidence_123"], ["AC_evidence", "AC_other"]
        )
        assert result["missing_artifacts"] == ["AC_other"]
        assert result["completeness_percentage"] == 50.0

    def test_no_required_artifacts_is_fully_complete(self, store):
        result = reporting.validate_artifact_completeness(store, "AC", [], [])
        assert result["completeness_percentage"] == 100.0

    def test_exact_match_without_timestamp_suffix(self, store):
        result = reporting.validate_artifact_completeness(
            store, "AC", ["AC_evidence"], ["AC_evidence"]
        )
        assert result["missing_artifacts"] == []

    def test_does_not_false_positive_on_unrelated_substring(self, store):
        # Regression test for the substring-matching bug in the original
        # gsa-pages implementation: a required name that is a substring of
        # an unrelated generated name must NOT count as present.
        result = reporting.validate_artifact_completeness(
            store, "AC", ["BACKUP_report_123"], ["AC"]
        )
        assert result["missing_artifacts"] == ["AC"]
        assert result["completeness_percentage"] == 0.0

    def test_requires_underscore_boundary_not_arbitrary_prefix(self, store):
        # "AC_evidence" must not match "AC_evidenceXYZ_123" (no underscore
        # boundary after the required name).
        result = reporting.validate_artifact_completeness(
            store, "AC", ["AC_evidenceXYZ_123"], ["AC_evidence"]
        )
        assert result["missing_artifacts"] == ["AC_evidence"]


class TestGenerateComplianceDashboard:
    def test_aggregates_across_reports(self, store):
        reports = [
            {
                "control_family": "AC",
                "compliance_status": "Compliant",
                "artifacts": ["a", "b"],
                "findings": [],
            },
            {
                "control_family": "AU",
                "compliance_status": "Generated",
                "artifacts": ["c"],
                "findings": ["f1"],
            },
        ]
        dashboard = reporting.generate_compliance_dashboard(store, reports)
        assert dashboard["control_families"] == ["AC", "AU"]
        assert dashboard["artifact_counts"] == [2, 1]
        assert dashboard["finding_counts"] == [0, 1]


class TestGenerateArtifactInventory:
    def test_counts_total(self, store):
        inventory = reporting.generate_artifact_inventory(store, "AC", ["a", "b", "c"])
        assert inventory["total_count"] == 3
        assert inventory["control_family"] == "AC"
