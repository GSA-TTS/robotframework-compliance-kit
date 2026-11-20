"""Shared GitHub REST/GraphQL client with host validation, retry, and pagination.

Extracted from gsa-pages (scripts/lib/github_client.py). Validates the URL
host before every request (defense-in-depth against SSRF or accidental
github.com-instead-of-api.github.com URLs), attaches consistent headers,
implements exponential backoff + Retry-After handling for 429/5xx, and
provides a repo-scoped `RepoIssuesClient` facade.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

__all__ = [
    "API_HOST",
    "API_ROOT",
    "API_VERSION",
    "DEFAULT_BACKOFF_BASE",
    "DEFAULT_BACKOFF_CAP",
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_TIMEOUT",
    "NO_RETRY",
    "RETRYABLE_STATUSES",
    "GitHubClient",
    "GitHubClientError",
    "RepoIssuesClient",
    "RetryConfig",
    "validate_github_api_url",
]

API_HOST = "api.github.com"
API_ROOT = f"https://{API_HOST}"
API_VERSION = "2022-11-28"
DEFAULT_TIMEOUT = 30
DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_BACKOFF_BASE = 1.0
DEFAULT_BACKOFF_CAP = 60.0
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryConfig:
    """Retry policy for :class:`GitHubClient`."""

    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    base: float = DEFAULT_BACKOFF_BASE
    cap: float = DEFAULT_BACKOFF_CAP


NO_RETRY = RetryConfig(max_attempts=1)


class GitHubClientError(RuntimeError):
    """Raised when the GitHub API returns an error status."""

    def __init__(self, method: str, url: str, status: int, detail: str) -> None:
        super().__init__(f"GitHub API {method} {url} failed: {status} {detail}")
        self.method = method
        self.url = url
        self.status = status
        self.detail = detail


def validate_github_api_url(url: str) -> str:
    """Return *url* if it targets the GitHub REST/GraphQL API, else raise ValueError."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Unsupported URL scheme for GitHub API request: {url}")
    if parsed.netloc != API_HOST:
        raise ValueError(f"Unsupported host for GitHub API request: {url}")
    return url


class GitHubClient:
    """Thin wrapper around ``urllib`` for GitHub REST + GraphQL."""

    def __init__(
        self,
        token: str,
        *,
        user_agent: str = "gsa-compliance-robot",
        timeout: int = DEFAULT_TIMEOUT,
        retry: RetryConfig | None = None,
        sleep: Any = time.sleep,
    ) -> None:
        self.token = token
        self.user_agent = user_agent
        self.timeout = timeout
        self.retry = retry or RetryConfig()
        self._sleep = sleep

    def _headers(self, *, has_body: bool) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": self.user_agent,
        }
        if has_body:
            headers["Content-Type"] = "application/json"
        return headers

    def request(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        api_url = validate_github_api_url(url)
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310 - host validated above
            api_url,
            data=data,
            headers=self._headers(has_body=payload is not None),
            method=method,
        )

        last_error: GitHubClientError | None = None
        for attempt in range(1, self.retry.max_attempts + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:  # noqa: S310
                    charset = response.headers.get_content_charset("utf-8")
                    content = response.read().decode(charset)
                    if not content:
                        return None
                    return json.loads(content)
            except urllib.error.HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")
                last_error = GitHubClientError(method, url, error.code, detail)
                if (
                    error.code in RETRYABLE_STATUSES
                    and attempt < self.retry.max_attempts
                ):
                    self._sleep(self._backoff_delay(attempt, error.headers))
                    continue
                raise last_error from error
        raise RuntimeError(  # pragma: no cover
            f"GitHub API {method} {url} exhausted retries without a recorded error"
        )

    def _backoff_delay(self, attempt: int, headers: Any) -> float:
        retry_after = None
        if headers is not None:
            retry_after = headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), self.retry.cap)
            except (TypeError, ValueError):
                pass
        return min(self.retry.cap, self.retry.base * (2 ** (attempt - 1)))

    def get(self, url: str) -> Any:
        return self.request("GET", url)

    def post(self, url: str, payload: dict[str, Any]) -> Any:
        return self.request("POST", url, payload)

    def patch(self, url: str, payload: dict[str, Any]) -> Any:
        return self.request("PATCH", url, payload)

    def delete(self, url: str) -> Any:
        return self.request("DELETE", url)

    def paginate(
        self,
        url: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> Iterator[dict[str, Any]]:
        """Yield items from a paginated REST endpoint."""
        separator = "&" if "?" in url else "?"
        page = 1
        while True:
            paged_url = f"{url}{separator}per_page={page_size}&page={page}"
            batch = self.get(paged_url)
            if not batch:
                return
            yield from batch
            if len(batch) < page_size:
                return
            page += 1

    def graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        return self.post(f"{API_ROOT}/graphql", payload)


class RepoIssuesClient:
    """Repo-scoped facade around :class:`GitHubClient` for issue operations."""

    def __init__(
        self, repo: str, token: str, *, user_agent: str = "gsa-compliance-robot"
    ) -> None:
        if "/" not in repo:
            raise ValueError(f"Repository must be in owner/repo format: {repo}")
        self.repo = repo
        self.owner, self.name = repo.split("/", 1)
        self.base_url = f"{API_ROOT}/repos/{self.owner}/{self.name}"
        self._client = GitHubClient(token=token, user_agent=user_agent)
        self._issues_by_title_cache: dict[str, dict[str, Any]] | None = None

    def list_issues(self, label: str, state: str = "open") -> list[dict[str, Any]]:
        url = f"{self.base_url}/issues?labels={urllib.parse.quote(label)}&state={state}"
        return list(self._client.paginate(url))

    def list_issues_with_labels(
        self, labels: list[str], state: str = "open"
    ) -> list[dict[str, Any]]:
        """List issues carrying any of *labels*, excluding pull requests."""
        seen: dict[int, dict[str, Any]] = {}
        for label in labels:
            for issue in self.list_issues(label, state=state):
                if "pull_request" in issue:
                    continue
                seen[int(issue["number"])] = issue
        return list(seen.values())

    def list_issue_comments(self, issue_number: int) -> list[dict[str, Any]]:
        url = f"{self.base_url}/issues/{issue_number}/comments"
        return list(self._client.paginate(url))

    list_comments = list_issue_comments

    def create_comment(self, issue_number: int, body: str) -> dict[str, Any]:
        return self._client.post(
            f"{self.base_url}/issues/{issue_number}/comments",
            {"body": body},
        )

    def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str],
        assignees: list[str] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"title": title, "body": body, "labels": labels}
        if assignees:
            payload["assignees"] = assignees
        return self._client.post(f"{self.base_url}/issues", payload)

    def update_issue(
        self,
        issue_number: int,
        *,
        body: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if body is not None:
            payload["body"] = body
        if labels is not None:
            payload["labels"] = labels
        if assignees is not None:
            payload["assignees"] = assignees
        return self._client.patch(f"{self.base_url}/issues/{issue_number}", payload)

    def close_issue(
        self, issue_number: int, state_reason: str = "completed"
    ) -> dict[str, Any]:
        return self._client.patch(
            f"{self.base_url}/issues/{issue_number}",
            {"state": "closed", "state_reason": state_reason},
        )

    def find_issue_by_title(self, title: str) -> dict[str, Any] | None:
        if self._issues_by_title_cache is None:
            self._issues_by_title_cache = self._load_issues_by_title()
        return self._issues_by_title_cache.get(title)

    def _load_issues_by_title(self) -> dict[str, dict[str, Any]]:
        query = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $cursor, states: [OPEN, CLOSED], orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number
        title
        body
        url
        state
        labels(first: 20) { nodes { name } }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""
        cache: dict[str, dict[str, Any]] = {}
        cursor: str | None = None
        while True:
            result = self._client.graphql(
                query,
                {"owner": self.owner, "name": self.name, "cursor": cursor},
            )
            issues = result["data"]["repository"]["issues"]
            for issue in issues["nodes"]:
                issue["labels"] = [
                    label["name"] for label in issue.get("labels", {}).get("nodes", [])
                ]
                issue_title = issue.get("title")
                if issue_title:
                    cache[issue_title] = issue
            page_info = issues["pageInfo"]
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]
        return cache
