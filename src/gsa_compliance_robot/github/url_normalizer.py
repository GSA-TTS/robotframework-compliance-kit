"""Canonicalize a GitHub `Repo` cell value from an inventory CSV.

Extracted from gsa-pages (tests/libraries/RepoUrlNormalizer.py) and
generalized with an optional `org_canonical` mapping (defaulting to GSA
organizations). Strips Markdown link wrappers, `/tree/...` suffixes,
trailing slashes, and whitespace.
"""

from __future__ import annotations

import re

__all__ = ["DEFAULT_ORG_CANONICAL", "RepoUrlNormalizer"]

DEFAULT_ORG_CANONICAL: dict[str, str] = {
    "gsa": "GSA",
    "gsa-tts": "GSA-TTS",
    "gsa-oes": "GSA-OES",
    "uswds": "uswds",
    "presidential-innovation-fellows": "presidential-innovation-fellows",
}

_TREE_SUFFIX = re.compile(r"/tree/.+$", re.IGNORECASE)
_MARKDOWN_LINK = re.compile(r"^\[([^\]]+)\]\([^)]+\)$")


class RepoUrlNormalizer:
    """Robot library that returns the canonical `github.com/<Org>/<Repo>` form."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, org_canonical: dict[str, str] | None = None) -> None:
        self._org_canonical = (
            dict(org_canonical)
            if org_canonical is not None
            else dict(DEFAULT_ORG_CANONICAL)
        )

    def normalize_repo_url(self, repo_url: str) -> str:
        """Return the canonical form of a Repo cell, or the trimmed input on failure."""
        if not repo_url:
            return ""
        value = repo_url.strip()
        if not value:
            return ""
        md_match = _MARKDOWN_LINK.match(value)
        if md_match:
            value = md_match.group(1).strip()
        value = _TREE_SUFFIX.sub("", value)
        value = value.rstrip("/")
        parts = value.split("/")
        if len(parts) < 3 or parts[0].lower() != "github.com":
            return value
        org = parts[1]
        repo = parts[2]
        canonical_org = self._org_canonical.get(org.lower(), org)
        return f"github.com/{canonical_org}/{repo}"
