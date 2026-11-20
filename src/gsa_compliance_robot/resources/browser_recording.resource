*** Settings ***
Documentation       Redacted operator-action recorder for RF Browser exploration.
...
...                 Backed by gsa_compliance_robot.browser_recording.
Library             Browser
Library             Collections
Library             gsa_compliance_robot.browser_recording    AS    GsaBrowserRecording


*** Keywords ***
Start Redacted Action Recording
    [Documentation]    Capture action metadata only. Never captures input values, cookies, or storage.
    ${page_ids}=    Get Page Ids    CURRENT
    ${page_id}=    Get From List    ${page_ids}    0
    ${script}=    GsaBrowserRecording.Get Recorder Script
    Evaluate JavaScript    ${None}    ${script}
    RETURN    ${page_id}

Save Redacted Action Recording
    [Documentation]    Persist allowlisted browser action events to <record_dir>/sanitized-actions.json.
    [Arguments]    ${record_dir}    ${target_page_id}
    ${page_ids}=    Get Page Ids    CURRENT
    IF    not ${page_ids}
        ${path}=    GsaBrowserRecording.Write Closed Page Recording    ${record_dir}
        Log    No recorder pages remain; saved an empty redacted recording.
        Log    Saved sanitized browser-action metadata to ${path}
        RETURN
    END
    ${target_open}=    Run Keyword And Return Status
    ...    List Should Contain Value    ${page_ids}    ${target_page_id}
    IF    ${target_open}
        Switch Page    ${target_page_id}
        Start Redacted Action Recording
    END
    ${status}    ${events}=    Run Keyword And Ignore Error
    ...    Evaluate JavaScript    ${None}    () => window.__gsaPagesActions || []
    IF    '${status}' == 'PASS'
        ${path}=    GsaBrowserRecording.Write Sanitized Events    ${events}    ${record_dir}
    ELSE
        ${path}=    GsaBrowserRecording.Write Closed Page Recording    ${record_dir}
        Log    Target page was closed; saved an empty redacted recording.
    END
    Log    Saved sanitized browser-action metadata to ${path}
