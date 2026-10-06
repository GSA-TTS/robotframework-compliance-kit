"""Environment variable loading and secret-masking helpers.

Extracted from gsa-pages (tests/resources/environment.resource +
tests/resources/auth.resource, which had duplicated this same logic) and
generalized for use by any GSA compliance/audit Robot Framework suite.

Design notes
------------
- `load_env_file` never raises if no .env file is found in any candidate
  location; callers decide whether that's fatal.
- Values are never logged — only key names. Callers that need to display a
  secret for debugging must use `mask_value` first.
- `mask_value` preserves the first/last 4 characters for values longer than
  8 characters (useful for confirming "is this the token I think it is"
  without leaking it), and fully masks shorter values.
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "load_env_file",
    "mask_value",
    "validate_required_env_vars",
]


def _candidate_env_paths(start_dir: str | Path) -> list[Path]:
    start = Path(start_dir)
    return [
        start / ".env",
        start.parent / ".env",
        start.parent.parent / ".env",
    ]


def load_env_file(start_dir: str | Path = ".") -> list[str]:
    """Load KEY=VALUE pairs from the first .env file found near `start_dir`.

    Search order: `start_dir/.env`, `start_dir/../.env`, `start_dir/../../.env`.
    Lines starting with `#` and blank lines are skipped. Inline comments
    (anything after a ` #`) are stripped from values. Values are exported
    into `os.environ`.

    Returns the list of variable names that were set (never the values) so
    callers can log what was loaded without risking a secret leak.
    """
    loaded: list[str] = []
    env_path: Path | None = None
    for candidate in _candidate_env_paths(start_dir):
        if candidate.is_file():
            env_path = candidate
            break

    if env_path is None:
        return loaded

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if "#" in value:
            value = value.split("#", 1)[0].strip()
        os.environ[key] = value
        loaded.append(key)

    return loaded


def mask_value(value: str) -> str:
    """Mask a sensitive string for safe logging.

    - len > 8:  first 4 + '****' + last 4
    - 0 < len <= 8: '****'
    - empty: ''
    """
    if not value:
        return ""
    length = len(value)
    if length > 8:
        return f"{value[:4]}****{value[-4:]}"
    return "****"


def validate_required_env_vars(*names: str) -> None:
    """Raise ValueError listing any of `names` not set (or empty) in os.environ."""
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise ValueError(
            f"Required environment variable(s) not set: {', '.join(missing)}"
        )
