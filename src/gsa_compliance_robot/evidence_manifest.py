"""Evidence run provenance and manifest library.

Extracted from gsa-pages (tests/libraries/EvidenceManifest.py) so any GSA
compliance or audit Robot Framework suite can record run provenance
(host, git SHA/ref, boolean env-var presence without leaking secret values),
SHA-256 digests of file and directory artifacts, and check results in a
deterministic `manifest.json`.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = ["EvidenceManifest", "ManifestArtifact"]


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    p = Path(path)
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_relpath(path: str | Path, base_dir: str | Path) -> str:
    p = Path(path)
    b = Path(base_dir)
    try:
        return str(p.resolve().relative_to(b.resolve()))
    except Exception:
        return str(p)


def _ensure_dir(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _read_env_subset(keys: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k in keys:
        v = os.environ.get(k)
        if v is not None and v != "":
            out[k] = v
    return out


def _hash_string(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass
class ManifestArtifact:
    """A single file or directory artifact produced during an evidence run."""

    path: str
    kind: str = "file"
    media_type: str = "application/octet-stream"
    sha256: str | None = None
    size_bytes: int | None = None
    generated_by: str | None = None
    description: str | None = None
    control_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def _dir_listing_sorted(root: Path) -> list[Path]:
    files = [p for p in root.rglob("*") if p.is_file()]
    files.sort(key=str)
    return files


def _sha256_directory(path: str | Path) -> str:
    root = Path(path)
    entries = []
    for p in _dir_listing_sorted(root):
        rel = str(p.relative_to(root))
        entries.append(
            {"path": rel, "sha256": _sha256_file(p), "size_bytes": p.stat().st_size}
        )
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return _hash_string(payload)


class EvidenceManifest:
    """Robot Framework library for writing an evidence run manifest with provenance."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self) -> None:
        self._manifest: dict[str, Any] = {}
        self._artifacts: list[dict[str, Any]] = []
        self._run_dir: str | None = None
        self._run_id: str | None = None

    def start_run(
        self,
        run_dir: str,
        run_name: str = "atu",
        source_system: str = "gsa-pages",
        initiated_by: str = "robotframework",
        command: str = "",
        git_sha: str = "",
        git_ref: str = "",
        target_org: str = "",
        inventory_path: str = "",
        env_presence_keys: list[str] | None = None,
        env_capture_keys: list[str] | None = None,
        schema: str = "gsa-pages.evidence-run-manifest.v1",
    ) -> str:
        """Initialize a new evidence run and return its `run_id`."""
        _ensure_dir(run_dir)
        run_id = _utc_now_iso().replace(":", "").replace("-", "").replace(".", "")
        self._run_id = run_id
        self._run_dir = run_dir

        presence: dict[str, bool] = {}
        if env_presence_keys:
            for k in env_presence_keys:
                presence[k] = os.environ.get(k) not in (None, "")
        captured_env = _read_env_subset(env_capture_keys or [])

        self._manifest = {
            "schema": schema,
            "run": {
                "id": run_id,
                "name": run_name,
                "source_system": source_system,
                "initiated_by": initiated_by,
                "created_at": _utc_now_iso(),
                "command": command,
            },
            "context": {
                "target_org": target_org,
                "inventory_path": inventory_path,
            },
            "provenance": {
                "host": {
                    "hostname": socket.gethostname(),
                    "fqdn": socket.getfqdn(),
                    "platform": platform.platform(),
                    "python": sys.version.split(" ")[0],
                },
                "git": {
                    "sha": git_sha,
                    "ref": git_ref,
                },
                "environment": {
                    "present": presence,
                    "captured": captured_env,
                },
            },
            "artifacts": [],
            "checks": [],
            "notes": [],
        }
        self._artifacts = []
        return run_id

    def add_note(self, note: str) -> None:
        if not self._manifest:
            raise RuntimeError(
                "EvidenceManifest.start_run must be called before add_note"
            )
        self._manifest["notes"].append({"at": _utc_now_iso(), "note": note})

    def add_artifact(
        self,
        path: str,
        kind: str = "file",
        media_type: str = "application/octet-stream",
        generated_by: str = "",
        description: str = "",
        control_ids: list[str] | None = None,
        tags: list[str] | None = None,
        metadata_json: str = "",
        base_dir: str = "",
    ) -> dict[str, Any]:
        """Register an artifact produced by the run, compute hashes, and store pointer."""
        if not self._manifest:
            raise RuntimeError(
                "EvidenceManifest.start_run must be called before add_artifact"
            )

        if kind not in ("file", "directory"):
            raise ValueError("kind must be 'file' or 'directory'")

        p = Path(path)
        if not p.exists():
            artifact = ManifestArtifact(
                path=path,
                kind=kind,
                media_type=media_type,
                sha256=None,
                size_bytes=None,
                generated_by=generated_by or None,
                description=description or None,
                control_ids=control_ids or [],
                tags=tags or [],
                metadata={"missing": True},
            )
            rec = artifact.__dict__
            self._artifacts.append(rec)
            return rec

        sha256: str | None
        size_bytes: int | None

        if kind == "directory":
            if not p.is_dir():
                raise ValueError(
                    f"Artifact kind 'directory' specified, but {p} is not a directory."
                )
            sha256 = _sha256_directory(p)
            size_bytes = None
        else:
            if not p.is_file():
                raise ValueError(
                    f"Artifact kind 'file' specified, but {p} is not a regular file."
                )
            sha256 = _sha256_file(p)
            size_bytes = p.stat().st_size

        metadata: dict[str, Any] = {}
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
            except Exception:
                metadata = {"metadata_json_parse_error": True, "raw": metadata_json}

        stored_path = _safe_relpath(p, base_dir) if base_dir else path

        artifact = ManifestArtifact(
            path=stored_path,
            kind="directory" if p.is_dir() else "file",
            media_type=media_type,
            sha256=sha256,
            size_bytes=size_bytes,
            generated_by=generated_by or None,
            description=description or None,
            control_ids=control_ids or [],
            tags=tags or [],
            metadata=metadata,
        )
        rec = artifact.__dict__
        self._artifacts.append(rec)
        return rec

    def add_check_result(
        self,
        check_id: str,
        title: str,
        passed: bool,
        details: str = "",
        control_ids: list[str] | None = None,
        related_artifact_paths: list[str] | None = None,
        metadata_json: str = "",
    ) -> None:
        if not self._manifest:
            raise RuntimeError(
                "EvidenceManifest.start_run must be called before add_check_result"
            )

        metadata: dict[str, Any] = {}
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
            except Exception:
                metadata = {"metadata_json_parse_error": True, "raw": metadata_json}

        self._manifest["checks"].append(
            {
                "at": _utc_now_iso(),
                "check_id": check_id,
                "title": title,
                "passed": bool(passed),
                "details": details,
                "control_ids": control_ids or [],
                "related_artifacts": related_artifact_paths or [],
                "metadata": metadata,
            }
        )

    def write_manifest(self, filename: str = "manifest.json") -> str:
        """Write the manifest to `<run_dir>/<filename>` and return the path."""
        if not self._manifest or self._run_dir is None or self._run_id is None:
            raise RuntimeError(
                "EvidenceManifest.start_run must be called before write_manifest"
            )

        self._manifest["artifacts"] = self._artifacts
        out_path = Path(self._run_dir) / filename
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(self._manifest, f, indent=2, sort_keys=True)

        return str(out_path)

    def get_manifest_json(self) -> str:
        """Return the current manifest as a JSON string."""
        if not self._manifest:
            raise RuntimeError(
                "EvidenceManifest.start_run must be called before get_manifest_json"
            )
        self._manifest["artifacts"] = self._artifacts
        return json.dumps(self._manifest, indent=2, sort_keys=True)
