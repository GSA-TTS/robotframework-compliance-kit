*** Settings ***
Documentation       Evidence run provenance and manifest keywords.
...
...                 Backed by gsa_compliance_robot.evidence_manifest.EvidenceManifest.
Library             gsa_compliance_robot.evidence_manifest.EvidenceManifest    AS    GsaEvidenceManifest


*** Keywords ***
Start Evidence Run
    [Documentation]    Initialize an evidence run in ${run_dir} and return its run_id.
    [Arguments]    ${run_dir}    ${run_name}=atu    ${source_system}=gsa-pages    ${command}=${EMPTY}
    ${run_id}=    GsaEvidenceManifest.Start Run
    ...    run_dir=${run_dir}    run_name=${run_name}    source_system=${source_system}    command=${command}
    RETURN    ${run_id}

Add Evidence Artifact
    [Documentation]    Register a file or directory artifact in the active manifest.
    [Arguments]    ${path}    ${kind}=file    ${media_type}=application/octet-stream    ${description}=${EMPTY}
    ${record}=    GsaEvidenceManifest.Add Artifact
    ...    path=${path}    kind=${kind}    media_type=${media_type}    description=${description}
    RETURN    ${record}

Add Evidence Check Result
    [Documentation]    Record a compliance check pass/fail entry in the active manifest.
    [Arguments]    ${check_id}    ${title}    ${passed}    ${details}=${EMPTY}
    GsaEvidenceManifest.Add Check Result
    ...    check_id=${check_id}    title=${title}    passed=${passed}    details=${details}

Add Evidence Note
    [Documentation]    Append a timestamped note to the active manifest.
    [Arguments]    ${note}
    GsaEvidenceManifest.Add Note    ${note}

Write Evidence Manifest
    [Documentation]    Write the active manifest to <run_dir>/<filename> and return the file path.
    [Arguments]    ${filename}=manifest.json
    ${path}=    GsaEvidenceManifest.Write Manifest    ${filename}
    RETURN    ${path}
