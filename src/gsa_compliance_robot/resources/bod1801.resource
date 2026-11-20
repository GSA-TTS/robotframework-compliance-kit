*** Settings ***
Documentation       DHS BOD 18-01 network posture checks (SPF, DMARC, TLS 1.2+, HTTPS, HSTS).
...
...                 Backed by gsa_compliance_robot.bod1801.BOD1801Checks.
Library             gsa_compliance_robot.bod1801.BOD1801Checks    AS    GsaBod1801


*** Keywords ***
Check BOD 18-01 Domain Posture
    [Documentation]    Run SPF, DMARC, TLS 1.2+, HTTPS, and HSTS probes for ${site_url}
    ...    and return a list of discrepancy dictionaries (`{feature, type, expected, actual}`).
    [Arguments]    ${site_url}
    ${findings}=    GsaBod1801.Check Domain    ${site_url}
    RETURN    ${findings}
