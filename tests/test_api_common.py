from __future__ import annotations

from types import SimpleNamespace

import pytest

from gsa_compliance_robot import api_common


class TestCreateApiHeaders:
    def test_default_accept_type(self):
        headers = api_common.create_api_headers("mytoken")
        assert headers == {
            "Authorization": "token mytoken",
            "Accept": "application/vnd.github.v3+json",
        }

    def test_custom_accept_type(self):
        headers = api_common.create_api_headers("mytoken", "application/json")
        assert headers["Accept"] == "application/json"


class TestCreateBearerHeaders:
    def test_default_accept_type(self):
        headers = api_common.create_bearer_headers("mytoken")
        assert headers == {
            "Authorization": "Bearer mytoken",
            "Accept": "application/json",
        }


class TestValidateApiResponse:
    def test_success_returns_json(self):
        response = SimpleNamespace(
            status_code=200, content=b"{}", json=lambda: {"ok": True}
        )
        assert api_common.validate_api_response(response) == {"ok": True}

    def test_wrong_status_raises(self):
        response = SimpleNamespace(status_code=404, content=b"{}", json=lambda: {})
        with pytest.raises(AssertionError, match="Expected status 200"):
            api_common.validate_api_response(response)

    def test_empty_content_raises(self):
        response = SimpleNamespace(status_code=200, content=b"", json=lambda: {})
        with pytest.raises(AssertionError, match="empty"):
            api_common.validate_api_response(response)

    def test_custom_expected_status(self):
        response = SimpleNamespace(
            status_code=201, content=b"{}", json=lambda: {"created": True}
        )
        result = api_common.validate_api_response(response, expected_status=201)
        assert result == {"created": True}
