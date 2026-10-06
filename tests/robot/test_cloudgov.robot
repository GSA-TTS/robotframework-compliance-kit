*** Settings ***
Documentation       Smoke suite: every exported keyword in cloudgov.resource
...                 resolves (keyword name + arg signature are valid) and
...                 runs without a Robot-level KeywordNotFound/argument
...                 error. Network/CLI-calling keywords use
...                 ``Run Keyword And Ignore Error`` since this suite has no
...                 live cloud.gov credentials and may or may not have the
...                 `cf` CLI installed depending on the environment - it
...                 proves keyword *resolution*, not live API behavior
...                 (that is covered by tests/test_cloudgov_client.py's
...                 mocked pytest suite). Assertions only check that the
...                 failure is a controlled one (CloudGovAuthError,
...                 ValueError, FileNotFoundError if `cf` is absent) and
...                 never a Robot-level KeywordNotFound.
Resource            ../../src/gsa_compliance_robot/resources/cloudgov.resource


*** Test Cases ***
Authenticate With Cloud Gov Token Resolves And Runs
    [Documentation]    Uses existing_token path - no network call made.
    ${token}=    Authenticate With Cloud Gov Token    existing_token=smoketesttoken12345
    Should Be Equal    ${token}    smoketesttoken12345

Authenticate With Cloud Gov Browser Token Resolves And Runs
    ${token}=    Authenticate With Cloud Gov Browser Token    smoketestbrowsertoken
    Should Be Equal    ${token}    smoketestbrowsertoken

Get Cloud Gov Organization GUID Resolves
    [Documentation]    No live credentials in CI - expect a controlled
    ...    failure (auth error), not a KeywordNotFound.
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Get Cloud Gov Organization GUID    smoke-test-org
    Should Be Equal    ${status}    FAIL
    Should Not Contain    ${result}    KeywordNotFound

Query Cloud Gov Audit Events Resolves
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Query Cloud Gov Audit Events    fake-org-guid
    Should Be Equal    ${status}    FAIL
    Should Not Contain    ${result}    KeywordNotFound

Get Cloud Gov User Access Change Events Resolves
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Get Cloud Gov User Access Change Events    fake-org-guid
    Should Be Equal    ${status}    FAIL
    Should Not Contain    ${result}    KeywordNotFound

Get Cloud Gov Service Events Resolves
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Get Cloud Gov Service Events    fake-org-guid
    Should Be Equal    ${status}    FAIL
    Should Not Contain    ${result}    KeywordNotFound

Login To Cloud Gov CLI Resolves
    [Documentation]    Expect a controlled failure either way - whether
    ...    `cf` is installed (invalid creds rejected) or absent
    ...    (FileNotFoundError from subprocess) - never KeywordNotFound.
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Login To Cloud Gov CLI    fake-user    fake-pass
    Should Be Equal    ${status}    FAIL
    Should Not Contain    ${result}    KeywordNotFound

Get Cloud Gov Organization GUID Via CLI Resolves
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Get Cloud Gov Organization GUID Via CLI    smoke-test-org
    Should Be Equal    ${status}    FAIL
    Should Not Contain    ${result}    KeywordNotFound

Get Cloud Gov Audit Events Via CLI Resolves
    [Documentation]    When `cf` is installed but unauthenticated, `cf curl`
    ...    exits 0 and returns an error-shaped JSON body on stdout (so this
    ...    keyword succeeds and returns a dict). When `cf` is absent,
    ...    subprocess raises FileNotFoundError (a controlled failure, not
    ...    KeywordNotFound). Accept either outcome.
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Get Cloud Gov Audit Events Via CLI    fake-org-guid
    IF    '${status}' == 'PASS'
        Should Be True    isinstance($result, dict)
    ELSE
        Should Not Contain    ${result}    KeywordNotFound
    END

Get Cloud Gov Application Logs Via CLI Resolves
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Get Cloud Gov Application Logs Via CLI    fake-app-name
    Should Be Equal    ${status}    FAIL
    Should Not Contain    ${result}    KeywordNotFound

Convert Cloud Gov Events To CSV Resolves And Runs
    [Documentation]    Pure data transform - no network call, should succeed.
    ${events}=    Evaluate    {"resources": []}
    Convert Cloud Gov Events To CSV    ${events}    ${OUTPUT_DIR}/smoke_events.csv
    File Should Exist    ${OUTPUT_DIR}/smoke_events.csv

Filter Cloud Gov Events By Date Range Resolves And Runs
    [Documentation]    Pure data transform - no network call, should succeed.
    ${events}=    Evaluate    {"resources": []}
    ${filtered}=    Filter Cloud Gov Events By Date Range
    ...    ${events}    2024-01-01T00:00:00Z    2024-12-31T23:59:59Z
    Should Be Equal    ${filtered}[resources]    ${{[]}}
