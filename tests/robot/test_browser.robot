*** Settings ***
Documentation       Smoke suite: every exported keyword in browser.resource
...                 resolves and runs without raising. Runs headless so it
...                 works unattended in CI.
...
...                 All assertions live in a single test case rather than
...                 being split across multiple test cases: the Browser
...                 library's default ``auto_closing_level=TEST`` closes
...                 the active context/page at the end of every test case
...                 (while leaving the browser process itself open), so a
...                 context/page created in one test is NOT visible to a
...                 later test in the same suite even though the browser
...                 and the ``${BROWSER_CONTEXT}``/``${PAGE}`` suite
...                 variables persist. Keeping the full
...                 init -> reuse -> health-check -> screenshot ->
...                 save-storage-state -> close sequence in one test
...                 avoids that pitfall and also matches how a real
...                 consumer suite uses these keywords (open once per test,
...                 not share across tests).
Resource            ../../src/gsa_compliance_robot/resources/browser.resource
Library             OperatingSystem

Suite Setup          Set Environment Variable    BROWSER_HEADLESS    true


*** Test Cases ***
Full Browser Lifecycle Resolves And Runs
    [Documentation]    Exercises init -> reuse -> health-check ->
    ...    screenshot -> save-storage-state -> close in one test case
    ...    (second Initialize Browser Safely call must reuse, not
    ...    recreate, the browser/context/page).
    Initialize Browser Safely
    Go To    about:blank

    Initialize Browser Safely

    Check Browser Health

    ${screenshot_path}=    Set Variable    ${OUTPUT_DIR}/smoke_screenshot.png
    Take Screenshot Artifact    ${screenshot_path}
    File Should Exist    ${screenshot_path}

    ${storage_path}=    Set Variable    ${OUTPUT_DIR}/smoke_storage_state.json
    Save Storage State To File    ${storage_path}
    File Should Exist    ${storage_path}

    Close Browser Safely
