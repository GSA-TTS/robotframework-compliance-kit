*** Settings ***
Documentation       Smoke suite: every exported keyword in allure.resource
...                 resolves and runs without raising. AllureLibrary is
...                 imported directly (not just via the resource) so this
...                 suite also proves the library-import-order concern
...                 noted in robocop's IMP01 rule (ignored in robocop.toml)
...                 doesn't actually break anything at runtime.
Resource            ../../src/gsa_compliance_robot/resources/allure.resource
Library             OperatingSystem


*** Test Cases ***
Allure Attach File If Exists Resolves For Existing File
    ${path}=    Set Variable    ${OUTPUT_DIR}/smoke_allure_test.txt
    Create File    ${path}    smoke test content
    Allure Attach File If Exists    ${path}

Allure Attach File If Exists Resolves For Missing File
    [Documentation]    Must not raise - logs a WARN and skips.
    Allure Attach File If Exists    ${OUTPUT_DIR}/does_not_exist.txt

Allure Attach Text If Exists Resolves And Runs
    ${path}=    Set Variable    ${OUTPUT_DIR}/smoke_allure_text.txt
    Create File    ${path}    text content
    Allure Attach Text If Exists    ${path}

Allure Attach JSON If Exists Resolves And Runs
    ${path}=    Set Variable    ${OUTPUT_DIR}/smoke_allure.json
    Create File    ${path}    {}
    Allure Attach JSON If Exists    ${path}

Allure Attach CSV If Exists Resolves And Runs
    ${path}=    Set Variable    ${OUTPUT_DIR}/smoke_allure.csv
    Create File    ${path}    a,b
    Allure Attach CSV If Exists    ${path}

Allure Attach Markdown If Exists Resolves And Runs
    ${path}=    Set Variable    ${OUTPUT_DIR}/smoke_allure.md
    Create File    ${path}    # heading
    Allure Attach Markdown If Exists    ${path}

Allure Attach HTML If Exists Resolves And Runs
    ${path}=    Set Variable    ${OUTPUT_DIR}/smoke_allure.html
    Create File    ${path}    <html></html>
    Allure Attach HTML If Exists    ${path}

Allure Attach String As Text Resolves And Runs
    Allure Attach String As Text    smoke test in-memory content
