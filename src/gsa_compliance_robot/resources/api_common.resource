*** Settings ***
Documentation       Common HTTP/API header-building and response-validation keywords.
Library             Collections
Library             RequestsLibrary
Library             gsa_compliance_robot.api_common    AS    GsaApiCommon


*** Keywords ***
Validate API Response
    [Documentation]    Validate response status and content; returns parsed JSON.
    [Arguments]    ${response}    ${expected_status}=200
    ${body}=    GsaApiCommon.Validate Api Response    ${response}    ${expected_status}
    RETURN    ${body}

Create API Headers
    [Documentation]    Build a `token <auth>`-style Authorization header dict
    ...    (GitHub classic PAT convention).
    [Arguments]    ${auth_token}    ${accept_type}=application/vnd.github.v3+json
    ${headers}=    GsaApiCommon.Create Api Headers    ${auth_token}    ${accept_type}
    RETURN    ${headers}

Create Bearer Headers
    [Documentation]    Build a `Bearer <auth>`-style Authorization header dict.
    [Arguments]    ${auth_token}    ${accept_type}=application/json
    ${headers}=    GsaApiCommon.Create Bearer Headers    ${auth_token}    ${accept_type}
    RETURN    ${headers}

Safe API Call
    [Documentation]    Make an API call with error handling; returns ${EMPTY} and
    ...    logs a WARN on failure instead of raising.
    [Arguments]    ${method}    ${url}    ${headers}=${EMPTY}    ${params}=${EMPTY}    ${data}=${EMPTY}
    ${response}=    Run Keyword And Ignore Error
    ...    ${method}    ${url}    headers=${headers}    params=${params}    data=${data}
    IF    '${response}[0]' == 'PASS'
        RETURN    ${response}[1]
    ELSE
        Log    API call failed: ${response}[1]    WARN
        RETURN    ${EMPTY}
    END
