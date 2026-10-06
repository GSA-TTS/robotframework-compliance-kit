*** Settings ***
Documentation       Compliance artifact and report generation keywords.
...
...                 Backed by gsa_compliance_robot.reporting.ArtifactStore. A
...                 suite must create the store once (via `Create Artifact Store`)
...                 before calling the other keywords in this resource.
Library             Collections
Library             gsa_compliance_robot.reporting    AS    GsaReporting


*** Keywords ***
Create Artifact Store
    [Documentation]    Create (and return) an ArtifactStore rooted at ${artifacts_dir}
    ...    (and optionally a separate ${reports_dir}). Call once per suite and
    ...    keep the returned object in a suite variable.
    [Arguments]    ${artifacts_dir}    ${reports_dir}=${NONE}
    ${store}=    GsaReporting.Create Artifact Store    ${artifacts_dir}    ${reports_dir}
    RETURN    ${store}

Generate Artifact Filename
    [Documentation]    Build a standardized artifact filename: <family>_<name>_<timestamp>.
    [Arguments]    ${control_family}    ${artifact_name}    ${timestamp}=${NONE}
    ${filename}=    GsaReporting.Generate Artifact Filename    ${control_family}    ${artifact_name}    ${timestamp}
    RETURN    ${filename}

Save Artifact JSON
    [Documentation]    Save a dict as <artifacts_dir>/<filename>.json via the given store.
    [Arguments]    ${store}    ${data}    ${filename}
    ${filepath}=    Call Method    ${store}    save_json    ${data}    ${filename}
    Log    Artifact saved: ${filepath}
    RETURN    ${filepath}

Save Artifact Text
    [Documentation]    Save text as <artifacts_dir>/<filename>.txt via the given store.
    [Arguments]    ${store}    ${content}    ${filename}
    ${filepath}=    Call Method    ${store}    save_text    ${content}    ${filename}
    Log    Artifact saved: ${filepath}
    RETURN    ${filepath}

Generate Control Family Report
    [Documentation]    Generate and persist (JSON + text) a report for one control family.
    [Arguments]    ${store}    ${control_family}    ${artifacts}    ${findings}    ${compliance_status}
    ${report}=    GsaReporting.Generate Control Family Report
    ...    ${store}    ${control_family}    ${artifacts}    ${findings}    ${compliance_status}
    RETURN    ${report}

Generate Executive Summary
    [Documentation]    Aggregate per-control-family reports into a cross-cutting
    ...    executive summary.
    [Arguments]    ${store}    ${all_reports}
    ${summary}=    GsaReporting.Generate Executive Summary    ${store}    ${all_reports}
    RETURN    ${summary}

Generate Artifact Inventory
    [Documentation]    Persist an inventory of all artifacts generated for one
    ...    control family.
    [Arguments]    ${store}    ${control_family}    ${artifacts_list}
    ${inventory}=    GsaReporting.Generate Artifact Inventory    ${store}    ${control_family}    ${artifacts_list}
    RETURN    ${inventory}

Validate Artifact Completeness
    [Documentation]    Check that every required artifact has a matching generated
    ...    artifact (substring match, tolerant of timestamp suffixes).
    [Arguments]    ${store}    ${control_family}    ${generated_artifacts}    ${required_artifacts}
    ${result}=    GsaReporting.Validate Artifact Completeness
    ...    ${store}    ${control_family}    ${generated_artifacts}    ${required_artifacts}
    RETURN    ${result}

Generate Compliance Dashboard
    [Documentation]    Build dashboard-ready aggregate data across all reports.
    [Arguments]    ${store}    ${all_reports}
    ${dashboard}=    GsaReporting.Generate Compliance Dashboard    ${store}    ${all_reports}
    RETURN    ${dashboard}
