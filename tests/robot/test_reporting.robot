*** Settings ***
Documentation       Smoke suite: every exported keyword in reporting.resource
...                 resolves and runs without raising.
Resource            ../../src/gsa_compliance_robot/resources/reporting.resource
Library             OperatingSystem


*** Test Cases ***
Create Artifact Store Resolves And Runs
    ${store}=    Create Artifact Store    ${OUTPUT_DIR}/smoke_artifacts
    Should Not Be Equal    ${store}    ${NONE}

Generate Artifact Filename Resolves And Runs
    ${filename}=    Generate Artifact Filename    AC    smoke_evidence
    Should Contain    ${filename}    AC_smoke_evidence_

Save Artifact JSON Resolves And Runs
    ${store}=    Create Artifact Store    ${OUTPUT_DIR}/smoke_artifacts
    ${data}=    Create Dictionary    key=value
    ${path}=    Save Artifact JSON    ${store}    ${data}    smoke_json_test
    File Should Exist    ${path}

Save Artifact Text Resolves And Runs
    ${store}=    Create Artifact Store    ${OUTPUT_DIR}/smoke_artifacts
    ${path}=    Save Artifact Text    ${store}    hello smoke test    smoke_text_test
    File Should Exist    ${path}

Generate Control Family Report Resolves And Runs
    ${store}=    Create Artifact Store    ${OUTPUT_DIR}/smoke_artifacts
    ${artifacts}=    Create List    artifact-1
    ${findings}=    Create List    finding-1
    ${report}=    Generate Control Family Report    ${store}    AC    ${artifacts}    ${findings}    Compliant
    Should Be Equal    ${report}[control_family]    AC

Generate Executive Summary Resolves And Runs
    ${store}=    Create Artifact Store    ${OUTPUT_DIR}/smoke_artifacts
    ${report1}=    Create Dictionary    compliance_status=Compliant    artifacts=${{['a']}}    findings=${{[]}}
    ${all_reports}=    Create List    ${report1}
    ${summary}=    Generate Executive Summary    ${store}    ${all_reports}
    Should Be Equal As Integers    ${summary}[total_families]    1

Generate Artifact Inventory Resolves And Runs
    ${store}=    Create Artifact Store    ${OUTPUT_DIR}/smoke_artifacts
    ${artifacts_list}=    Create List    artifact-1    artifact-2
    ${inventory}=    Generate Artifact Inventory    ${store}    AC    ${artifacts_list}
    Should Be Equal As Integers    ${inventory}[total_count]    2

Validate Artifact Completeness Resolves And Runs
    ${store}=    Create Artifact Store    ${OUTPUT_DIR}/smoke_artifacts
    ${generated}=    Create List    AC_evidence_123
    ${required}=    Create List    AC_evidence
    ${result}=    Validate Artifact Completeness    ${store}    AC    ${generated}    ${required}
    Should Be Equal As Numbers    ${result}[completeness_percentage]    100.0

Generate Compliance Dashboard Resolves And Runs
    ${store}=    Create Artifact Store    ${OUTPUT_DIR}/smoke_artifacts
    ${report1}=    Create Dictionary
    ...    control_family=AC    compliance_status=Compliant    artifacts=${{['a']}}    findings=${{[]}}
    ${all_reports}=    Create List    ${report1}
    ${dashboard}=    Generate Compliance Dashboard    ${store}    ${all_reports}
    Should Contain    ${dashboard}[control_families]    AC
