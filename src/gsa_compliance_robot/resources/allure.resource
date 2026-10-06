*** Settings ***
Documentation       Allure reporting helpers — convenience keywords for attaching
...                 artifacts and checking file existence before attaching.
...
...                 Label hierarchy (epic > feature > story > severity) is applied
...                 via Robot Framework [Tags] using the allure.* tag prefix
...                 convention:
...
...                     [Tags]    allure.epic:My Compliance Suite
...                               allure.feature:Some Validation
...                               allure.severity:normal
...
...                 Import this resource in any suite that wants enriched Allure
...                 output alongside the --listener allure_robotframework flag.
Library             AllureLibrary
Library             OperatingSystem
Library             gsa_compliance_robot.allure_helpers.AllureHelpers    AS    GsaAllure


*** Keywords ***
Allure Attach File If Exists
    [Documentation]    Attach a file to the current Allure test result only if it
    ...    exists. Silently skips (logs a warning) if the file is not found.
    [Arguments]    ${path}    ${name}=${EMPTY}    ${attachment_type}=TEXT
    GsaAllure.Allure Attach File If Exists    ${path}    ${name}    ${attachment_type}

Allure Attach Text If Exists
    [Documentation]    Attach a plain-text file to the current Allure test result.
    [Arguments]    ${path}    ${name}=${EMPTY}
    GsaAllure.Allure Attach Text If Exists    ${path}    ${name}

Allure Attach JSON If Exists
    [Documentation]    Attach a JSON file to the current Allure test result.
    [Arguments]    ${path}    ${name}=${EMPTY}
    GsaAllure.Allure Attach Json If Exists    ${path}    ${name}

Allure Attach CSV If Exists
    [Documentation]    Attach a CSV file to the current Allure test result.
    [Arguments]    ${path}    ${name}=${EMPTY}
    GsaAllure.Allure Attach Csv If Exists    ${path}    ${name}

Allure Attach Markdown If Exists
    [Documentation]    Attach a Markdown file as plain text to the current Allure
    ...    test result.
    [Arguments]    ${path}    ${name}=${EMPTY}
    GsaAllure.Allure Attach Markdown If Exists    ${path}    ${name}

Allure Attach HTML If Exists
    [Documentation]    Attach an HTML file to the current Allure test result.
    [Arguments]    ${path}    ${name}=${EMPTY}
    GsaAllure.Allure Attach Html If Exists    ${path}    ${name}

Allure Attach String As Text
    [Documentation]    Attach an in-memory string as a text attachment.
    [Arguments]    ${content}    ${name}=output
    GsaAllure.Allure Attach String As Text    ${content}    ${name}
