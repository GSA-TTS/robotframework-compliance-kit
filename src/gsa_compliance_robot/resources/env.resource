*** Settings ***
Documentation       Environment variable loading and secret-masking keywords.
...
...                 Backed by gsa_compliance_robot.env (pure Python, no Robot
...                 dependencies). Import this resource in any suite that
...                 needs .env loading or value masking.
Library             gsa_compliance_robot.env    AS    GsaEnv


*** Keywords ***
Load Environment Variables
    [Documentation]    Loads KEY=VALUE pairs from the nearest .env file (searches
    ...    ${CURDIR}, its parent, and its grandparent) into os.environ. Never
    ...    logs values — only variable names.
    [Arguments]    ${start_dir}=${CURDIR}
    ${loaded}=    GsaEnv.Load Env File    ${start_dir}
    RETURN    ${loaded}

Mask Sensitive Value
    [Documentation]    Masks a sensitive string for safe logging (first4****last4,
    ...    or **** for short values, or empty for empty input).
    [Arguments]    ${value}
    ${masked}=    GsaEnv.Mask Value    ${value}
    RETURN    ${masked}

Validate Environment Variables
    [Documentation]    Fails if any of the given environment variable names are
    ...    unset or empty.
    [Arguments]    @{required_vars}
    GsaEnv.Validate Required Env Vars    @{required_vars}
