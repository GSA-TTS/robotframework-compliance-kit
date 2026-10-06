*** Settings ***
Documentation       Smoke suite: every exported keyword in redaction.resource
...                 resolves and runs without raising.
Resource            ../../src/gsa_compliance_robot/resources/redaction.resource


*** Test Cases ***
Register Secret Resolves And Runs
    Register Secret    smoketestsecretvalue12345

Register Secret Ignores Empty Value
    [Documentation]    Must not raise on empty input (guarded by the
    ...    keyword's own IF before delegating to the library).
    Register Secret    ${EMPTY}

Register Secret Pattern Resolves And Runs
    Register Secret Pattern    SMOKE-[0-9]{4}
