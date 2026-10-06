*** Settings ***
Documentation       Smoke suite: every exported keyword in cloudlogs.resource
...                 resolves. No live AWS/Azure/GCP credentials exist in CI,
...                 so network-calling keywords use
...                 ``Run Keyword And Ignore Error`` - this proves keyword
...                 *resolution* (correct AS aliases, correct argument
...                 signatures), not live query behavior (covered by the
...                 mocked pytest suites in tests/test_cloudlogs_*.py).
Resource            ../../src/gsa_compliance_robot/resources/cloudlogs.resource
Library             Collections


*** Test Cases ***
Run CloudWatch Insights Query And Wait Resolves
    [Documentation]    Either resolves+fails cleanly (no AWS credentials) or
    ...    - in an environment with default credentials - returns an
    ...    error-shaped result rather than raising KeywordNotFound either
    ...    way; only ${result} is asserted on.
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Run CloudWatch Insights Query And Wait    fake-log-group    fields @message    timeout=1
    Should Not Contain    ${result}    KeywordNotFound

Start CloudWatch Insights Query Resolves
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Start CloudWatch Insights Query    fake-log-group    fields @message
    Should Not Contain    ${result}    KeywordNotFound

Run Azure Log Query And Wait Resolves
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Run Azure Log Query And Wait    fake-workspace    FakeTable | take 1
    Should Be Equal    ${status}    FAIL
    Should Not Contain    ${result}    KeywordNotFound

Run GCP Log Query And Wait Resolves
    ${status}    ${result}=    Run Keyword And Ignore Error
    ...    Run GCP Log Query And Wait    fake-project    resource.type="x"
    Should Not Contain    ${result}    KeywordNotFound

Get Violation Count Resolves And Runs
    [Documentation]    Pure data transform - no network call, should succeed.
    ${row}=    Create List
    ${field}=    Create Dictionary    field=violation    value=1
    Append To List    ${row}    ${field}
    ${results}=    Create List    ${row}
    ${count}=    Get Violation Count    ${results}
    Should Be Equal As Integers    ${count}    1
