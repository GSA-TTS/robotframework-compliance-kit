*** Settings ***
Documentation       Unified cloud.gov API/CLI client keywords.
...
...                 Merges the previously-duplicated cloud.gov integrations from
...                 M-26-14 (CloudGovAPI.resource + CloudGovCLI.resource) and
...                 gsa-pages (cloudgov_auth.resource + cloudgov_api.resource).
...                 Always calls the real cloud.gov API/CLI — there is no
...                 mock-data mode in this library; consumers that need offline
...                 behavior should mock at their own test boundary.
Library             OperatingSystem
Library             gsa_compliance_robot.cloudgov.client.CloudGovClient    AS    CloudGov
Library             gsa_compliance_robot.cloudgov.helpers    AS    CloudGovHelpers


*** Keywords ***
Authenticate With Cloud Gov Token
    [Documentation]    Authenticate via OAuth2 password grant, or normalize an
    ...    externally-supplied token (e.g., CF_OAUTH_TOKEN). Returns the token.
    [Arguments]    ${username}=${NONE}    ${password}=${NONE}    ${existing_token}=${NONE}
    ${token}=    CloudGov.Authenticate With Token    ${username}    ${password}    ${existing_token}
    RETURN    ${token}

Authenticate With Cloud Gov Browser Token
    [Documentation]    Register a bearer token already extracted from an
    ...    established browser session (see browser.resource for session
    ...    setup). This client does not perform browser automation itself.
    [Arguments]    ${token}
    ${registered}=    CloudGov.Authenticate With Browser Token    ${token}
    RETURN    ${registered}

Get Cloud Gov Organization GUID
    [Documentation]    Return the GUID for an organization name via the REST API.
    [Arguments]    ${org_name}
    ${guid}=    CloudGov.Get Organization Guid    ${org_name}
    RETURN    ${guid}

Query Cloud Gov Audit Events
    [Documentation]    Query /v3/audit_events for an organization, optionally
    ...    filtered by comma-separated event types.
    [Arguments]    ${org_guid}    ${event_types}=${NONE}
    ${events}=    CloudGov.Query Audit Events    ${org_guid}    ${event_types}
    RETURN    ${events}

Get Cloud Gov User Access Change Events
    [Documentation]    Audit events for space-role (developer/auditor/manager)
    ...    add/remove actions in an organization.
    [Arguments]    ${org_guid}
    ${events}=    CloudGov.Get User Access Change Events    ${org_guid}
    RETURN    ${events}

Get Cloud Gov Service Events
    [Documentation]    Audit events for service/service-binding/service-instance
    ...    lifecycle actions in an organization.
    [Arguments]    ${org_guid}
    ${events}=    CloudGov.Get Service Events    ${org_guid}
    RETURN    ${events}

Login To Cloud Gov CLI
    [Documentation]    Authenticate using `cf login` (requires the `cf` CLI on PATH).
    [Arguments]    ${username}    ${password}
    CloudGov.Login Via Cli    ${username}    ${password}

Get Cloud Gov Organization GUID Via CLI
    [Documentation]    Return the GUID for a named organization via `cf org --guid`.
    [Arguments]    ${org_name}
    ${guid}=    CloudGov.Get Organization Guid Via Cli    ${org_name}
    RETURN    ${guid}

Get Cloud Gov Audit Events Via CLI
    [Documentation]    Retrieve audit events via `cf curl` for an organization.
    [Arguments]    ${org_guid}    ${event_filter}=${NONE}
    ${events}=    CloudGov.Get Audit Events Via Cli    ${org_guid}    ${event_filter}
    RETURN    ${events}

Get Cloud Gov Application Logs Via CLI
    [Documentation]    Return recent application logs via `cf logs <app> --recent`.
    [Arguments]    ${app_name}
    ${logs}=    CloudGov.Get Application Logs Via Cli    ${app_name}
    RETURN    ${logs}

Convert Cloud Gov Events To CSV
    [Documentation]    Convert a cloud.gov audit-events JSON payload to CSV text
    ...    and write it to ${csv_file}.
    [Arguments]    ${events_json}    ${csv_file}
    ${csv_content}=    CloudGovHelpers.Convert Json Events To Csv    ${events_json}
    Create File    ${csv_file}    ${csv_content}
    Log    CSV file created: ${csv_file}

Filter Cloud Gov Events By Date Range
    [Documentation]    Return a copy of the events JSON filtered to [start_date, end_date]
    ...    (ISO 8601 strings).
    [Arguments]    ${events_json}    ${start_date}    ${end_date}
    ${filtered}=    CloudGovHelpers.Filter Events By Date Range    ${events_json}    ${start_date}    ${end_date}
    RETURN    ${filtered}
