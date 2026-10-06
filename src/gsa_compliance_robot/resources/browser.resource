*** Settings ***
Documentation       Browser (Playwright / rf-browser) session lifecycle keywords.
...
...    Single source of truth for browser init/close/health-check/screenshot/
...    storage-state keywords. Suites that need Playwright must import both
...    this resource AND `Library    Browser` directly (Browser itself is not
...    re-exported here so pure-API suites don't trigger the rfbrowser
...    listener when it isn't needed).
Library             Browser
Library             gsa_compliance_robot.browser_session.BrowserSession    AS    GsaBrowserSession


*** Keywords ***
Initialize Browser Safely
    [Documentation]    Initialize browser, context, and page with proper error
    ...    handling. Reuses an existing browser/context/page when available;
    ...    honours BROWSER_HEADLESS (default: false).
    GsaBrowserSession.Initialize Browser Safely

Check Browser Health
    [Documentation]    Check if browser is alive; reinitialize if not.
    GsaBrowserSession.Check Browser Health

Close Browser Safely
    [Documentation]    Close browser context and all browsers, swallowing errors.
    GsaBrowserSession.Close Browser Safely

Take Screenshot Artifact
    [Documentation]    Take a screenshot and save it to ${filepath}.
    [Arguments]    ${filepath}    ${locator}=${EMPTY}
    IF    '${locator}' != '${EMPTY}'
        GsaBrowserSession.Take Screenshot Artifact    ${filepath}    ${locator}
    ELSE
        GsaBrowserSession.Take Screenshot Artifact    ${filepath}
    END

Save Storage State To File
    [Documentation]    Save the current browser context's storage state
    ...    (cookies, localStorage) to ${filepath}.
    [Arguments]    ${filepath}
    GsaBrowserSession.Save Storage State To File    ${filepath}
