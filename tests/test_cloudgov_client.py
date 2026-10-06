from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gsa_compliance_robot.cloudgov.client import (
    CloudGovAuthError,
    CloudGovClient,
    SERVICE_EVENT_TYPES,
    USER_ACCESS_CHANGE_EVENT_TYPES,
)


class TestAuthenticateWithToken:
    def test_uses_existing_token_without_network_call(self):
        client = CloudGovClient()
        token = client.authenticate_with_token(existing_token="rawtoken123")
        assert token == "rawtoken123"
        assert client._token == "rawtoken123"

    def test_strips_bearer_prefix_case_insensitive(self):
        client = CloudGovClient()
        token = client.authenticate_with_token(existing_token="Bearer rawtoken123")
        assert token == "rawtoken123"

    def test_raises_without_credentials_or_token(self):
        client = CloudGovClient()
        with pytest.raises(CloudGovAuthError):
            client.authenticate_with_token()

    @patch("requests.post")
    def test_password_grant_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: {"access_token": "granted-token"}
        )
        client = CloudGovClient()
        token = client.authenticate_with_token(username="u", password="p")
        assert token == "granted-token"
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_password_grant_failure_raises(self, mock_post):
        mock_post.return_value = MagicMock(status_code=401)
        client = CloudGovClient()
        with pytest.raises(CloudGovAuthError):
            client.authenticate_with_token(username="u", password="wrong")


class TestOrganizationAndAuditEvents:
    def _authed_client(self):
        client = CloudGovClient()
        client.authenticate_with_token(existing_token="tok12345678")
        return client

    @patch("requests.get")
    def test_get_organization_guid(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"resources": [{"guid": "org-guid-1"}]},
        )
        client = self._authed_client()
        guid = client.get_organization_guid("my-org")
        assert guid == "org-guid-1"

    @patch("requests.get")
    def test_get_organization_guid_not_found(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"resources": []})
        client = self._authed_client()
        with pytest.raises(ValueError, match="Organization not found"):
            client.get_organization_guid("missing-org")

    @patch("requests.get")
    def test_get_organization_guid_http_error(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        client = self._authed_client()
        with pytest.raises(CloudGovAuthError):
            client.get_organization_guid("my-org")

    def test_query_audit_events_without_auth_raises(self):
        client = CloudGovClient()
        with pytest.raises(CloudGovAuthError, match="Not authenticated"):
            client.query_audit_events("org-guid-1")

    @patch("requests.get")
    def test_query_audit_events_includes_type_filter(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"resources": []})
        client = self._authed_client()
        client.query_audit_events("org-guid-1", "audit.user.create")
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["types"] == "audit.user.create"

    @patch("requests.get")
    def test_get_user_access_change_events_uses_correct_types(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"resources": []})
        client = self._authed_client()
        client.get_user_access_change_events("org-guid-1")
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["types"] == USER_ACCESS_CHANGE_EVENT_TYPES

    @patch("requests.get")
    def test_get_service_events_uses_correct_types(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"resources": []})
        client = self._authed_client()
        client.get_service_events("org-guid-1")
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["types"] == SERVICE_EVENT_TYPES


class TestCliBackend:
    @patch("subprocess.run")
    def test_login_via_cli_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        client = CloudGovClient()
        client.login_via_cli("user", "pass")
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_login_via_cli_failure_raises(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="bad creds")
        client = CloudGovClient()
        with pytest.raises(CloudGovAuthError, match="bad creds"):
            client.login_via_cli("user", "wrong")

    @patch("subprocess.run")
    def test_get_organization_guid_via_cli(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="org-guid-xyz\n", stderr="")
        client = CloudGovClient()
        guid = client.get_organization_guid_via_cli("my-org")
        assert guid == "org-guid-xyz"

    @patch("subprocess.run")
    def test_get_audit_events_via_cli(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"resources": []}', stderr=""
        )
        client = CloudGovClient()
        events = client.get_audit_events_via_cli("org-guid-1")
        assert events == {"resources": []}

    @patch("subprocess.run")
    def test_get_audit_events_via_cli_failure_raises(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="cf not logged in")
        client = CloudGovClient()
        with pytest.raises(CloudGovAuthError):
            client.get_audit_events_via_cli("org-guid-1")

    @patch("subprocess.run")
    def test_get_application_logs_via_cli(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="log line 1\n", stderr="")
        client = CloudGovClient()
        logs = client.get_application_logs_via_cli("my-app")
        assert "log line 1" in logs
