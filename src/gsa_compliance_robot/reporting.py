"""Compliance artifact and report generation helpers.

Extracted from gsa-pages (tests/resources/common.resource — the artifact
persistence half, as opposed to the Browser-dependent half which lives in
`browser_session.py` — plus the whole of tests/resources/reporting.resource).

None of this logic is GSA-Pages-specific: filename conventions, JSON/text
artifact persistence, control-family report generation, executive
summaries, dashboards, and completeness validation are useful to any
compliance/audit Robot suite (including M-26-14's EL-criteria findings,
which previously used a bespoke markdown generator in
`scripts/generate_report.py`).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

__all__ = [
    "ArtifactStore",
    "create_artifact_store",
    "generate_artifact_filename",
    "generate_control_family_report",
    "generate_executive_summary",
    "generate_artifact_inventory",
    "validate_artifact_completeness",
    "generate_compliance_dashboard",
]


def _timestamp(fmt: str = "%Y%m%d%H%M%S") -> str:
    return datetime.now().strftime(fmt)


def generate_artifact_filename(
    control_family: str, artifact_name: str, timestamp: str | None = None
) -> str:
    """Build a standardized artifact filename: `<family>_<name>_<timestamp>`."""
    ts = timestamp or _timestamp()
    return f"{control_family}_{artifact_name}_{ts}"


@dataclass
class ArtifactStore:
    """Persists compliance artifacts (JSON/text) under a fixed directory tree.

    Mirrors gsa-pages's `${ARTIFACTS_DIR}`/`${REPORTS_DIR}` convention so
    consumer repos can point this at their own `results/artifacts` (or
    equivalent) directory without re-implementing the persistence logic.
    """

    artifacts_dir: str
    reports_dir: str | None = None

    def __post_init__(self) -> None:
        if self.reports_dir is None:
            self.reports_dir = self.artifacts_dir
        os.makedirs(self.artifacts_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

    def save_json(self, data: dict[str, Any], filename: str) -> str:
        """Save `data` as `<artifacts_dir>/<filename>.json`; returns the path written."""
        filepath = os.path.join(self.artifacts_dir, f"{filename}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=True)
        return filepath

    def save_text(self, content: str, filename: str) -> str:
        """Save `content` as `<artifacts_dir>/<filename>.txt`; returns the path written."""
        filepath = os.path.join(self.artifacts_dir, f"{filename}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def generate_artifact(self, control_id: str, filename: str) -> str:
        """Write a minimal standardized artifact (`control_id`, `generated_at`, `status`)."""
        data = {
            "control_id": control_id,
            "generated_at": _timestamp(),
            "status": "generated",
        }
        filepath = os.path.join(self.artifacts_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return filepath


def create_artifact_store(
    artifacts_dir: str, reports_dir: str | None = None
) -> ArtifactStore:
    """Module-level constructor so Robot can call this as a keyword
    (`GsaReporting.Create Artifact Store`) — Robot Framework resolves
    library keywords from functions/methods, not bare class names, so a
    thin wrapper avoids surprising callers of the `.resource` file.
    """
    return ArtifactStore(artifacts_dir=artifacts_dir, reports_dir=reports_dir)


def _text_report(report_data: dict[str, Any]) -> str:
    lines = [
        "=" * 40,
        "COMPLIANCE ASSESSMENT REPORT",
        "=" * 40,
        "",
        f"Control Family: {report_data['control_family']}",
        f"Generated: {report_data['timestamp']}",
        f"Status: {report_data['compliance_status']}",
        "",
        "ARTIFACTS GENERATED:",
        "-" * 19,
    ]
    for artifact in report_data["artifacts"]:
        lines.append(f"\u2022 {artifact}")
    lines.extend(["", "FINDINGS:", "-" * 9])
    for finding in report_data["findings"]:
        lines.append(f"\u2022 {finding}")
    return "\n".join(lines)


def generate_control_family_report(
    store: ArtifactStore,
    control_family: str,
    artifacts: list[str],
    findings: list[str],
    compliance_status: str,
) -> dict[str, Any]:
    """Generate and persist (JSON + text) a comprehensive report for one control family."""
    report_data = {
        "control_family": control_family,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "artifacts": artifacts,
        "findings": findings,
        "compliance_status": compliance_status,
        "report_type": "Control Family Assessment",
    }
    filename = generate_artifact_filename(control_family, "assessment_report")
    store.save_json(report_data, filename)
    store.save_text(_text_report(report_data), filename)
    return report_data


def _executive_text_summary(summary: dict[str, Any]) -> str:
    lines = [
        "=" * 40,
        "COMPLIANCE EXECUTIVE SUMMARY",
        "=" * 40,
        "",
        f"Generated: {summary['timestamp']}",
        "",
        "OVERVIEW:",
        "-" * 9,
        f"Total Control Families: {summary['total_families']}",
        f"Compliant Families: {summary['compliant_families']}",
        f"Total Artifacts: {summary['total_artifacts']}",
        "",
    ]
    if summary["total_families"]:
        rate = (summary["compliant_families"] / summary["total_families"]) * 100
    else:
        rate = 0.0
    lines.append(f"Compliance Rate: {rate}%")
    lines.extend(["", "CRITICAL FINDINGS:", "-" * 18])
    if summary["critical_findings"]:
        lines.extend(f"\u2022 {finding}" for finding in summary["critical_findings"])
    else:
        lines.append("\u2022 No critical findings identified")
    return "\n".join(lines)


def generate_executive_summary(
    store: ArtifactStore, all_reports: list[dict[str, Any]]
) -> dict[str, Any]:
    """Aggregate per-control-family reports into a cross-cutting executive summary."""
    compliant_count = 0
    total_artifacts = 0
    critical_findings: list[str] = []

    for report in all_reports:
        if report["compliance_status"] in ("Compliant", "Generated"):
            compliant_count += 1
        total_artifacts += len(report["artifacts"])
        for finding in report["findings"]:
            if "CRITICAL" in finding or "HIGH" in finding:
                critical_findings.append(finding)

    summary = {
        "report_type": "Executive Summary",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_families": len(all_reports),
        "compliant_families": compliant_count,
        "total_artifacts": total_artifacts,
        "critical_findings": critical_findings,
    }

    filename = generate_artifact_filename("EXECUTIVE", "summary_report")
    store.save_json(summary, filename)
    store.save_text(_executive_text_summary(summary), filename)
    return summary


def generate_artifact_inventory(
    store: ArtifactStore, control_family: str, artifacts_list: list[str]
) -> dict[str, Any]:
    """Persist an inventory of all artifacts generated for one control family."""
    inventory = {
        "control_family": control_family,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "artifacts": artifacts_list,
        "total_count": len(artifacts_list),
    }
    filename = generate_artifact_filename(control_family, "artifact_inventory")
    store.save_json(inventory, filename)
    return inventory


def validate_artifact_completeness(
    store: ArtifactStore,
    control_family: str,
    generated_artifacts: list[str],
    required_artifacts: list[str],
) -> dict[str, Any]:
    """Check that every entry in `required_artifacts` has a matching generated artifact.

    Matching is substring-based (a required name is considered present if
    it appears as a substring of any generated artifact name) to tolerate
    timestamp/suffix variation in generated filenames.
    """
    missing = [
        required
        for required in required_artifacts
        if not any(required in generated for generated in generated_artifacts)
    ]
    total_required = len(required_artifacts)
    completeness = (
        ((total_required - len(missing)) / total_required) * 100
        if total_required
        else 100.0
    )
    result = {
        "control_family": control_family,
        "required_artifacts": required_artifacts,
        "generated_artifacts": generated_artifacts,
        "missing_artifacts": missing,
        "completeness_percentage": completeness,
    }
    filename = generate_artifact_filename(control_family, "completeness_validation")
    store.save_json(result, filename)
    return result


def generate_compliance_dashboard(
    store: ArtifactStore, all_reports: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build dashboard-ready aggregate data (families/status/counts) across all reports."""
    dashboard = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "control_families": [r["control_family"] for r in all_reports],
        "compliance_status": [r["compliance_status"] for r in all_reports],
        "artifact_counts": [len(r["artifacts"]) for r in all_reports],
        "finding_counts": [len(r["findings"]) for r in all_reports],
    }
    filename = generate_artifact_filename("DASHBOARD", "compliance_dashboard")
    store.save_json(dashboard, filename)
    return dashboard
