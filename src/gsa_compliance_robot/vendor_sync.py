"""Vendor-sync CLI for gsa-compliance-robot `.resource` files.

Copies the package's `.resource` files into a consumer repository directory
(e.g., `tests/resources/vendor/`) with a `# VENDORED from gsa-compliance-robot`
banner and writes a deterministic `vendor.lock.json` recording per-file
SHA-256 digests. Provides `--check` / `check` mode for CI drift detection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from gsa_compliance_robot import __version__

LOCKFILE_NAME = "vendor.lock.json"
RESOURCES_DIR = Path(__file__).resolve().parent / "resources"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _header_line(version: str) -> str:
    return f"# VENDORED from gsa-compliance-robot v{version} \u2014 do not edit\n"


def _render_vendored_resource(source_path: Path, version: str) -> bytes:
    raw = source_path.read_text(encoding="utf-8")
    # Strip any pre-existing VENDORED banner if re-rendering
    lines = raw.splitlines(keepends=True)
    if lines and lines[0].startswith("# VENDORED from gsa-compliance-robot"):
        raw = "".join(lines[1:])
    rendered = _header_line(version) + raw
    if not rendered.endswith("\n"):
        rendered += "\n"
    return rendered.encode("utf-8")


def _expected_bundle(
    version: str, resources_dir: Path = RESOURCES_DIR
) -> tuple[dict[str, bytes], bytes]:
    """Return `(filename -> rendered_bytes, lockfile_bytes)`."""
    if not resources_dir.is_dir():
        raise FileNotFoundError(f"Package resources directory not found: {resources_dir}")

    rendered_files: dict[str, bytes] = {}
    lock_entries: dict[str, dict[str, str]] = {}

    for src in sorted(resources_dir.glob("*.resource")):
        content = _render_vendored_resource(src, version)
        rendered_files[src.name] = content
        lock_entries[src.name] = {
            "version": version,
            "sha256": _sha256_bytes(content),
        }

    lock_payload: dict[str, Any] = {
        "schema_version": 1,
        "package": "gsa-compliance-robot",
        "version": version,
        "resources": lock_entries,
    }
    lock_bytes = (json.dumps(lock_payload, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    return rendered_files, lock_bytes


def sync_resources(
    dest: Path,
    version: str = __version__,
    resources_dir: Path = RESOURCES_DIR,
) -> dict[str, Any]:
    """Write vendored `.resource` files and `vendor.lock.json` into `dest`."""
    rendered_files, lock_bytes = _expected_bundle(version, resources_dir)
    dest.mkdir(parents=True, exist_ok=True)

    for name, content in rendered_files.items():
        (dest / name).write_bytes(content)

    (dest / LOCKFILE_NAME).write_bytes(lock_bytes)
    return json.loads(lock_bytes.decode("utf-8"))


def check_resources(
    dest: Path,
    version: str | None = None,
    resources_dir: Path = RESOURCES_DIR,
) -> list[str]:
    """Verify `dest` matches the expected vendored `.resource` bundle and lockfile."""
    errors: list[str] = []
    lock_path = dest / LOCKFILE_NAME
    if not lock_path.is_file():
        return [f"Missing lockfile: {lock_path}"]

    try:
        lock_on_disk = json.loads(lock_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Invalid JSON in {lock_path}: {exc}"]

    effective_version = version or str(lock_on_disk.get("version") or __version__)
    rendered_files, expected_lock_bytes = _expected_bundle(
        effective_version, resources_dir
    )

    actual_lock_bytes = lock_path.read_bytes()
    if actual_lock_bytes != expected_lock_bytes:
        errors.append(
            f"Lockfile drift detected in {lock_path} (expected v{effective_version})"
        )

    for name, expected_bytes in sorted(rendered_files.items()):
        target_file = dest / name
        if not target_file.is_file():
            errors.append(f"Missing vendored resource: {name}")
            continue
        actual_bytes = target_file.read_bytes()
        if actual_bytes != expected_bytes:
            errors.append(
                f"Content/SHA-256 mismatch for {name}: expected "
                f"{_sha256_bytes(expected_bytes)}, got {_sha256_bytes(actual_bytes)}"
            )

    for existing in sorted(dest.glob("*.resource")):
        if existing.name not in rendered_files:
            errors.append(f"Unexpected extra resource file in {dest}: {existing.name}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gsa-robot-vendor",
        description=(
            "Vendor-sync CLI for gsa-compliance-robot .resource files "
            "(copies pinned .resource files with vendor.lock.json and verifies drift)."
        ),
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["sync", "check", "help"],
        help="Command to execute: 'sync', 'check', or 'help'.",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path("tests/resources/vendor"),
        help="Destination directory for vendored .resource files (default: tests/resources/vendor).",
    )
    parser.add_argument(
        "--version",
        dest="pkg_version",
        default=None,
        help=f"Package version string to stamp (default: {__version__}).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify destination matches expected vendored files without writing.",
    )
    args = parser.parse_args(argv)

    if args.command == "help":
        parser.print_help()
        return 0

    if args.command == "check" or args.check:
        errors = check_resources(dest=args.dest, version=args.pkg_version)
        if errors:
            for err in errors:
                print(f"gsa-robot-vendor: DRIFT: {err}", file=sys.stderr)
            return 1
        print(f"gsa-robot-vendor: OK ({args.dest} is in sync)")
        return 0

    effective_version = args.pkg_version or __version__
    payload = sync_resources(dest=args.dest, version=effective_version)
    count = len(payload.get("resources", {}))
    print(
        f"gsa-robot-vendor: synced {count} .resource files "
        f"(v{effective_version}) -> {args.dest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
