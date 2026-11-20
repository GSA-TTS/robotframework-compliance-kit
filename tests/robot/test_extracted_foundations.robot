*** Settings ***
Documentation       Smoke suite exercising every exported keyword in
...                 bod1801.resource, vulnerability_timeline.resource,
...                 evidence_manifest.resource, and github.resource.
Library             Collections
Library             OperatingSystem
Resource            ../../src/gsa_compliance_robot/resources/bod1801.resource
Resource            ../../src/gsa_compliance_robot/resources/vulnerability_timeline.resource
Resource            ../../src/gsa_compliance_robot/resources/evidence_manifest.resource
Resource            ../../src/gsa_compliance_robot/resources/github.resource


*** Test Cases ***
BOD 18-01 Keywords Resolve And Run
    ${findings}=    Check BOD 18-01 Domain Posture    ${EMPTY}
    Length Should Be    ${findings}    0

Vulnerability Timeline Keywords Resolve And Run
    ${days}=    Get GSA Remediation Deadline    critical    ${TRUE}
    Should Be Equal As Integers    ${days}    15
    ${norm}=    Normalize Vulnerability Severity    MEDIUM
    Should Be Equal    ${norm}    moderate
    ${status}=    Get Vulnerability Remediation Status    2026-01-01T00:00:00Z    high
    Should Be Equal    ${status}[severity]    high
    ${alerts}=    Create List
    ${summary}=    Analyze Vulnerability Alerts Timeline    ${alerts}
    ${report}=    Format Vulnerability Timeline Report    ${summary}    GSA-TTS/gsa-pages
    Should Contain    ${report}    Vulnerability Timeline Report

Evidence Manifest Keywords Resolve And Run
    ${run_dir}=    Set Variable    ${TEMPDIR}/rf_smoke_manifest
    ${run_id}=    Start Evidence Run    ${run_dir}
    Should Not Be Empty    ${run_id}
    ${art_path}=    Set Variable    ${run_dir}/sample.txt
    Create File    ${art_path}    smoke
    ${rec}=    Add Evidence Artifact    ${art_path}
    Should Not Be Empty    ${rec}[sha256]
    Add Evidence Check Result    AC-2    Access check    ${TRUE}
    Add Evidence Note    Smoke test note
    ${manifest_file}=    Write Evidence Manifest
    File Should Exist    ${manifest_file}
    Remove Directory    ${run_dir}    recursive=${TRUE}

GitHub Keywords Resolve And Run
    ${norm_url}=    Normalize Repository URL    github.com/gsa-tts/gsa-pages/tree/main/
    Should Be Equal    ${norm_url}    github.com/GSA-TTS/gsa-pages
    ${api_url}=    Validate GitHub API URL    https://api.github.com/repos/GSA-TTS/gsa-pages
    Should Be Equal    ${api_url}    https://api.github.com/repos/GSA-TTS/gsa-pages
