*** Settings ***
Documentation       Smoke suite: every exported keyword in api_common.resource
...                 resolves and runs without raising.
Resource            ../../src/gsa_compliance_robot/resources/api_common.resource


*** Test Cases ***
Create API Headers Resolves And Runs
    ${headers}=    Create API Headers    footoken123
    Should Be Equal    ${headers}[Authorization]    token footoken123

Create Bearer Headers Resolves And Runs
    ${headers}=    Create Bearer Headers    footoken123
    Should Be Equal    ${headers}[Authorization]    Bearer footoken123

Validate API Response Resolves And Runs
    ${response}=    Evaluate
    ...    type('R', (), {'status_code': 200, 'content': b'{}', 'json': lambda self: {'ok': True}})()
    ${body}=    Validate API Response    ${response}
    Should Be Equal    ${body}[ok]    ${True}

Safe API Call Resolves For A Known-Failing Target
    [Documentation]    Points at a reserved, non-routable TEST-NET address
    ...    (RFC 5737) so this never depends on network availability or an
    ...    external service being up — it only proves the keyword resolves
    ...    and its error-handling branch returns ${EMPTY} instead of raising.
    ${result}=    Safe API Call    GET    http://192.0.2.1/    timeout=1
    Should Be Equal    ${result}    ${EMPTY}
