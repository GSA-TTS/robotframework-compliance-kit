*** Settings ***
Documentation       Smoke suite: every exported keyword in env.resource is
...                 called at least once so a Robot-level keyword-resolution
...                 regression (typo'd AS alias, renamed Python function,
...                 wrong library import order, etc.) fails CI instead of
...                 only being caught by manual ``robot --dryrun`` runs.
...
...                 This suite intentionally does NOT assert on most return
...                 values — it exists to prove every keyword resolves and
...                 executes without raising, not to re-test business logic
...                 already covered by tests/test_env.py.
Resource            ../../src/gsa_compliance_robot/resources/env.resource
Library             OperatingSystem


*** Test Cases ***
Load Environment Variables Resolves And Runs
    [Documentation]    No .env file is expected to exist at ${CURDIR}; the
    ...    keyword must not raise even when nothing is found.
    ${loaded}=    Load Environment Variables    ${CURDIR}
    Should Be True    isinstance($loaded, list)

Mask Sensitive Value Resolves And Runs
    ${masked}=    Mask Sensitive Value    supersecretvalue12345
    Should Not Be Equal    ${masked}    supersecretvalue12345
    Should Contain    ${masked}    ****

Mask Sensitive Value Handles Empty Input
    ${masked}=    Mask Sensitive Value    ${EMPTY}
    Should Be Equal    ${masked}    ${EMPTY}

Validate Environment Variables Resolves And Runs
    Set Environment Variable    SMOKE_TEST_VAR_ONE    present
    Validate Environment Variables    SMOKE_TEST_VAR_ONE
