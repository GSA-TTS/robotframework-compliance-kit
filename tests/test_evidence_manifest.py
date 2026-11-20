from __future__ import annotations

import json
from pathlib import Path

import pytest

from gsa_compliance_robot.evidence_manifest import EvidenceManifest


def test_evidence_manifest_lifecycle_and_hashing(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TARGET_ORG", "GSA-TTS")
    monkeypatch.setenv("MANIFEST_TEST_SECRET", "do-not-capture")

    m = EvidenceManifest()
    run_id = m.start_run(
        run_dir=str(tmp_path),
        run_name="atu",
        source_system="gsa-pages",
        env_presence_keys=["MANIFEST_TEST_SECRET", "MISSING_KEY"],
        env_capture_keys=["TARGET_ORG"],
    )
    assert run_id

    art_file = tmp_path / "evidence.json"
    art_file.write_text('{"ok": true}\n', encoding="utf-8")
    rec_file = m.add_artifact(
        str(art_file),
        kind="file",
        media_type="application/json",
        control_ids=["AC-2"],
        metadata_json='{"source": "unit"}',
        base_dir=str(tmp_path),
    )
    assert rec_file["path"] == "evidence.json"
    assert rec_file["sha256"]

    sub_dir = tmp_path / "bundle"
    sub_dir.mkdir()
    (sub_dir / "item.txt").write_text("hello\n", encoding="utf-8")
    rec_dir = m.add_artifact(str(sub_dir), kind="directory")
    assert rec_dir["kind"] == "directory"
    assert rec_dir["sha256"]

    missing_rec = m.add_artifact(str(tmp_path / "nonexistent.txt"))
    assert missing_rec["metadata"] == {"missing": True}

    m.add_note("Run completed")
    m.add_check_result(
        "AC-2-check",
        "Verify team access",
        True,
        details="All teams matched",
        metadata_json="not-json-with-secret",
    )

    out_path = m.write_manifest("manifest.json")
    payload = json.loads(Path(out_path).read_text(encoding="utf-8"))
    assert payload["provenance"]["environment"]["present"]["MANIFEST_TEST_SECRET"] is True
    assert payload["provenance"]["environment"]["present"]["MISSING_KEY"] is False
    assert payload["provenance"]["environment"]["captured"]["TARGET_ORG"] == "GSA-TTS"
    assert len(payload["artifacts"]) == 3
    assert len(payload["checks"]) == 1
    assert payload["checks"][0]["metadata"] == {"metadata_json_parse_error": True}
    assert "raw" not in payload["checks"][0]["metadata"]
    assert json.loads(m.get_manifest_json())["run"]["id"] == run_id


@pytest.mark.parametrize(
    "bad_filename",
    [
        "/tmp/out.json",
        "../../out.json",
        "nested/out.json",
        "manifest.txt",
        "..",
        "",
    ],
)
def test_write_manifest_rejects_traversal_and_non_json_filenames(
    tmp_path: Path, bad_filename: str
):
    m = EvidenceManifest()
    m.start_run(run_dir=str(tmp_path))
    with pytest.raises(ValueError, match="single .json filename"):
        m.write_manifest(bad_filename)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "GITHUB_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
        "DATABASE_URL",
        "UNLISTED_CONFIG_VAR",
    ],
)
def test_start_run_rejects_sensitive_or_unallowlisted_env_capture_keys(
    tmp_path: Path, forbidden_key: str
):
    m = EvidenceManifest()
    with pytest.raises(ValueError, match="not permitted in env_capture_keys"):
        m.start_run(run_dir=str(tmp_path), env_capture_keys=[forbidden_key])


def test_evidence_manifest_guards_before_start_run():
    m = EvidenceManifest()
    with pytest.raises(RuntimeError):
        m.add_note("fail")
    with pytest.raises(RuntimeError):
        m.add_artifact("x")
    with pytest.raises(RuntimeError):
        m.add_check_result("id", "t", True)
    with pytest.raises(RuntimeError):
        m.write_manifest()
    with pytest.raises(RuntimeError):
        m.get_manifest_json()
