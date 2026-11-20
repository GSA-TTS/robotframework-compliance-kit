from __future__ import annotations

import io
import json
import urllib.error
from typing import Any
from unittest.mock import patch

import pytest

from gsa_compliance_robot.github import (
    API_ROOT,
    NO_RETRY,
    GitHubClient,
    GitHubClientError,
    RepoIssuesClient,
    RepoUrlNormalizer,
    RetryConfig,
    validate_github_api_url,
)
from gsa_compliance_robot.github import client as gc


def test_repo_url_normalizer():
    n = RepoUrlNormalizer()
    assert (
        n.normalize_repo_url("github.com/gsa/data-strategy/tree/main/")
        == "github.com/GSA/data-strategy"
    )
    assert (
        n.normalize_repo_url("[github.com/gsa-tts/handbook](https://github.com/gsa-tts/handbook)")
        == "github.com/GSA-TTS/handbook"
    )
    assert n.normalize_repo_url("") == ""
    assert n.normalize_repo_url("   ") == ""
    assert n.normalize_repo_url("not a url") == "not a url"
    custom = RepoUrlNormalizer(org_canonical={"my-org": "My-Org"})
    assert custom.normalize_repo_url("github.com/my-org/app") == "github.com/My-Org/app"


def test_validate_github_api_url():
    url = f"{API_ROOT}/repos/GSA-TTS/gsa-pages/issues"
    assert validate_github_api_url(url) == url
    with pytest.raises(ValueError, match="scheme"):
        validate_github_api_url("http://api.github.com/repos/x/y")
    with pytest.raises(ValueError, match="host"):
        validate_github_api_url("https://github.com/repos/x/y")


class _FakeHeaders:
    def get_content_charset(self, default: str) -> str:
        return default


class _FakeResponse:
    def __init__(self, payload: Any) -> None:
        self._body = json.dumps(payload).encode("utf-8") if payload is not None else b""
        self.headers = _FakeHeaders()

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *a: object) -> None:
        return None


def test_github_client_verbs_retry_and_repo_issues_client():
    responses: list[Any] = [
        {"login": "octocat"},
        [{"number": 1}, {"number": 2}],
        {"id": 10},
        {"state": "closed"},
        None,
    ]

    def fake_urlopen(req: urllib.request.Request, *, timeout: int) -> _FakeResponse:
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return _FakeResponse(item)

    with patch.object(gc.urllib.request, "urlopen", fake_urlopen):
        client = GitHubClient(token="t", retry=NO_RETRY)
        assert client.get(f"{API_ROOT}/user") == {"login": "octocat"}
        repo_client = RepoIssuesClient("GSA-TTS/gsa-pages", token="t")
        assert len(repo_client.list_issues_with_labels(["atu"])) == 2
        assert repo_client.create_comment(1, "hello") == {"id": 10}
        assert repo_client.close_issue(1) == {"state": "closed"}
        assert client.delete(f"{API_ROOT}/repos/x/y/collaborators/u") is None

    # Retry on 503 with Retry-After
    sleeps: list[float] = []
    err_503 = urllib.error.HTTPError(
        url=f"{API_ROOT}/user",
        code=503,
        msg="Unavailable",
        hdrs={"Retry-After": "1"},  # type: ignore[arg-type]
        fp=io.BytesIO(b"busy"),
    )
    responses = [err_503, {"ok": True}]
    with patch.object(gc.urllib.request, "urlopen", fake_urlopen):
        c2 = GitHubClient(
            token="t",
            retry=RetryConfig(max_attempts=2, base=0.1, cap=5.0),
            sleep=sleeps.append,
        )
        assert c2.get(f"{API_ROOT}/user") == {"ok": True}
    assert sleeps == [1.0]

    # 404 raises GitHubClientError immediately
    err_404 = urllib.error.HTTPError(
        url=f"{API_ROOT}/user",
        code=404,
        msg="Not Found",
        hdrs={},  # type: ignore[arg-type]
        fp=io.BytesIO(b"missing"),
    )
    responses = [err_404]
    with patch.object(gc.urllib.request, "urlopen", fake_urlopen):
        with pytest.raises(GitHubClientError) as exc:
            client.get(f"{API_ROOT}/user")
        assert exc.value.status == 404
