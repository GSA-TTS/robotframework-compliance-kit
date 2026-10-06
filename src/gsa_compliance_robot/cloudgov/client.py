"""Unified cloud.gov client.

Merges the previously-duplicated cloud.gov integrations:
  - M-26-14: resources/CloudGovAPI.resource (OAuth password-grant + REST),
    resources/CloudGovCLI.resource (`cf` CLI wrapper)
  - gsa-pages: tests/resources/cloudgov_auth.resource (browser SSO + `cf`
    CLI placeholder), tests/resources/cloudgov_api.resource (mock-data only)

This client supports three authentication strategies behind one interface
so Robot keywords can call `Query Audit Events` etc. without caring which
backend a given environment uses:

  - "token":   OAuth2 password grant against login.fr.cloud.gov (or an
               externally-supplied CF_OAUTH_TOKEN), then REST calls via
               `requests`.
  - "cf_cli":  Shells out to the `cf` CLI (`cf login`, `cf curl`). Useful in
               environments where interactive SSO already happened via `cf
               login --sso` and a token refresh is undesirable.
  - "browser": Delegates session establishment to a Playwright/Browser
               session the caller already set up (e.g., via
               `browser_session.py`); this client only builds headers from
               a token the caller extracts from that session. Kept as a
               documented strategy name for Robot callers that need to
               branch on `CLOUDGOV_AUTH_METHOD`; the actual browser
               automation lives in `browser_session.py` + consumer-side
               `.resource` files, not here.

Real-API-first: unlike gsa-pages's original `cloudgov_api.resource` (which
returned hardcoded mock dictionaries), this client always calls the real
cloud.gov API/CLI. Callers that need offline/unit-test behavior should mock
`requests`/`subprocess` at the test boundary, not inside this module.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Literal

AuthMethod = Literal["token", "cf_cli", "browser"]

_DEFAULT_API_URL = "https://api.fr.cloud.gov"
_DEFAULT_OAUTH_URL = "https://login.fr.cloud.gov/oauth/token"

# Audit event type groups mirrored from both source implementations.
USER_ACCESS_CHANGE_EVENT_TYPES = (
    "audit.user.space_developer_add,audit.user.space_developer_remove,"
    "audit.user.space_auditor_add,audit.user.space_auditor_remove,"
    "audit.user.space_manager_add,audit.user.space_manager_remove"
)
SERVICE_EVENT_TYPES = (
    "audit.service.create,audit.service.delete,audit.service.update,"
    "audit.service_binding.create,audit.service_binding.delete,"
    "audit.service_instance.create,audit.service_instance.delete,"
    "audit.service_instance.update"
)


class CloudGovAuthError(RuntimeError):
    """Raised when authentication to cloud.gov fails."""


class CloudGovClient:
    """Unified cloud.gov API/CLI client with pluggable auth.

    Example (token auth):
        client = CloudGovClient(api_url="https://api.fr.cloud.gov")
        client.authenticate_with_token(username, password)
        org_guid = client.get_organization_guid("my-org")
        events = client.query_audit_events(org_guid)

    Example (cf CLI auth, already-logged-in session):
        client = CloudGovClient(auth_method="cf_cli")
        org_guid = client.get_organization_guid_via_cli("my-org")
        events = client.get_audit_events_via_cli(org_guid)
    """

    def __init__(
        self,
        api_url: str = _DEFAULT_API_URL,
        auth_method: AuthMethod = "token",
    ) -> None:
        self.api_url = api_url
        self.auth_method = auth_method
        self._token: str | None = None

    # ---- token/REST backend -------------------------------------------------

    def authenticate_with_token(
        self,
        username: str | None = None,
        password: str | None = None,
        existing_token: str | None = None,
        oauth_url: str = _DEFAULT_OAUTH_URL,
    ) -> str:
        """Authenticate via OAuth2 password grant, or normalize an externally-supplied token.

        If `existing_token` is provided (e.g., a CF_OAUTH_TOKEN already
        present in the environment), it is normalized (leading "bearer "
        stripped) and used directly — no network call is made. Otherwise
        `username`/`password` are required and a password-grant request is
        made against `oauth_url`.
        """
        import requests

        if existing_token:
            token = existing_token
            if token.lower().startswith("bearer "):
                token = token[7:]
            self._token = token
            return token

        if not username or not password:
            raise CloudGovAuthError(
                "authenticate_with_token requires either existing_token or "
                "both username and password"
            )

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": "cf",
            "client_secret": "",
        }
        response = requests.post(oauth_url, data=data, headers=headers, timeout=30)
        if response.status_code != 200:
            raise CloudGovAuthError(
                f"OAuth token request failed with status {response.status_code}"
            )
        token = response.json()["access_token"]
        self._token = token
        return token

    def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            raise CloudGovAuthError(
                "Not authenticated — call authenticate_with_token first"
            )
        return {"Authorization": f"Bearer {self._token}"}

    def get_organization_guid(self, org_name: str) -> str:
        """Return the GUID for an organization name via the REST API."""
        import requests

        response = requests.get(
            f"{self.api_url}/v3/organizations",
            params={"names": org_name},
            headers=self._auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise CloudGovAuthError(
                f"Failed to look up organization '{org_name}': "
                f"status {response.status_code}"
            )
        resources = response.json().get("resources", [])
        if not resources:
            raise ValueError(f"Organization not found: {org_name}")
        return resources[0]["guid"]

    def query_audit_events(
        self, org_guid: str, event_types: str | None = None
    ) -> dict[str, Any]:
        """Query `/v3/audit_events` for an organization, optionally filtered by type."""
        import requests

        params = {"organization_guids": org_guid}
        if event_types:
            params["types"] = event_types

        response = requests.get(
            f"{self.api_url}/v3/audit_events",
            params=params,
            headers=self._auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise CloudGovAuthError(
                f"audit_events query failed: status {response.status_code}"
            )
        return response.json()

    def get_user_access_change_events(self, org_guid: str) -> dict[str, Any]:
        """Audit events for space-role (developer/auditor/manager) add/remove."""
        return self.query_audit_events(org_guid, USER_ACCESS_CHANGE_EVENT_TYPES)

    def get_service_events(self, org_guid: str) -> dict[str, Any]:
        """Audit events for service/service-binding/service-instance lifecycle."""
        return self.query_audit_events(org_guid, SERVICE_EVENT_TYPES)

    # ---- cf CLI backend -------------------------------------------------

    def login_via_cli(
        self, username: str, password: str, skip_ssl_validation: bool = True
    ) -> None:
        """Authenticate using `cf login` (requires the `cf` CLI on PATH)."""
        cmd = ["cf", "login", "-a", self.api_url, "-u", username, "-p", password]
        if skip_ssl_validation:
            cmd.append("--skip-ssl-validation")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise CloudGovAuthError(f"cf login failed: {result.stderr}")

    def get_organization_guid_via_cli(self, org_name: str) -> str:
        """Return the GUID for a named organization via `cf org --guid`."""
        result = subprocess.run(
            ["cf", "org", org_name, "--guid"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise CloudGovAuthError(f"cf org lookup failed: {result.stderr}")
        return result.stdout.strip()

    def get_audit_events_via_cli(
        self, org_guid: str, event_filter: str | None = None
    ) -> dict[str, Any]:
        """Retrieve audit events via `cf curl` for an organization."""
        query = f"/v3/audit_events?organization_guids={org_guid}"
        if event_filter:
            query += f"&types={event_filter}"
        result = subprocess.run(
            ["cf", "curl", query], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise CloudGovAuthError(f"cf curl failed: {result.stderr}")
        return json.loads(result.stdout)

    def get_user_access_changes_via_cli(self, org_guid: str) -> dict[str, Any]:
        """CLI equivalent of `get_user_access_change_events`."""
        return self.get_audit_events_via_cli(org_guid, USER_ACCESS_CHANGE_EVENT_TYPES)

    def get_application_logs_via_cli(self, app_name: str) -> str:
        """Return recent application logs via `cf logs <app> --recent`."""
        result = subprocess.run(
            ["cf", "logs", app_name, "--recent"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise CloudGovAuthError(f"cf logs failed: {result.stderr}")
        return result.stdout
