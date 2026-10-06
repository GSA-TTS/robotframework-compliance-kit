"""Common HTTP/API helpers shared across GSA compliance Robot suites.

Extracted from gsa-pages (tests/resources/api_common.resource).
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "create_api_headers",
    "create_bearer_headers",
    "validate_api_response",
]


def create_api_headers(
    auth_token: str, accept_type: str = "application/vnd.github.v3+json"
) -> dict[str, str]:
    """Build a `token <auth>` style Authorization header dict (GitHub classic PAT style)."""
    return {"Authorization": f"token {auth_token}", "Accept": accept_type}


def create_bearer_headers(
    auth_token: str, accept_type: str = "application/json"
) -> dict[str, str]:
    """Build a `Bearer <auth>` style Authorization header dict."""
    return {"Authorization": f"Bearer {auth_token}", "Accept": accept_type}


def validate_api_response(response: Any, expected_status: int = 200) -> Any:
    """Assert `response.status_code == expected_status` and content is non-empty.

    Returns `response.json()`. Raises AssertionError on mismatch, matching the
    behavior of the original Robot keyword (`Should Be Equal As Integers` +
    `Should Not Be Empty`).
    """
    status_code = getattr(response, "status_code", None)
    if status_code != expected_status:
        raise AssertionError(
            f"Expected status {expected_status}, got {status_code}"
        )
    content = getattr(response, "content", None)
    if not content:
        raise AssertionError("Response content is empty")
    return response.json()
