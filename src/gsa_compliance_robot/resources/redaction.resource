*** Settings ***
Documentation       Registers runtime secrets with the RedactionListener so they
...                 are masked in output.xml, log.html, and report.html.
...
...                 Load this resource in any suite that mints or handles bearer
...                 tokens so the raw value is never written to Robot artifacts.
...                 Works in tandem with
...                 `--listener gsa_compliance_robot.redaction.RedactionListener`.
Library             gsa_compliance_robot.redaction.RedactionListener    AS    RedactionListener


*** Keywords ***
Register Secret
    [Documentation]    Register a runtime secret (e.g., a freshly minted installation
    ...    token) so the RedactionListener masks every future occurrence of it
    ...    in Robot output.
    [Arguments]    ${value}
    IF    '${value}' == '' or '${value}' == '${EMPTY}'    RETURN
    RedactionListener.Register Secret    ${value}

Register Secret Pattern
    [Documentation]    Register an additional regex pattern to mask, for secret
    ...    shapes not covered by the built-in GitHub/JWT/Bearer/AWS patterns.
    [Arguments]    ${pattern}
    RedactionListener.Register Pattern    ${pattern}
