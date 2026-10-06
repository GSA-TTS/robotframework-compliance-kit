*** Settings ***
Documentation       Cloud log-query keywords (AWS CloudWatch Insights, Azure Log
...                 Analytics, GCP Cloud Logging) behind one consistent
...                 start/run-and-wait shape.
...
...                 Generalized from M-26-14's resources/common.resource (AWS),
...                 resources/azure_common.resource, and resources/gcp_common.resource,
...                 which each implemented the same pattern against a different SDK.
Library             gsa_compliance_robot.cloudlogs.aws.AwsInsightsClient    region=us-east-1    AS    AwsLogs
Library             gsa_compliance_robot.cloudlogs.azure.AzureMonitorClient    AS    AzureLogs
Library             gsa_compliance_robot.cloudlogs.gcp.GcpLoggingClient    AS    GcpLogs


*** Keywords ***
Run CloudWatch Insights Query And Wait
    [Documentation]    Start a CloudWatch Logs Insights query and poll until
    ...    completion or timeout. Returns (results, metadata).
    [Arguments]    ${log_group}    ${query}    ${start_time}=${NONE}    ${end_time}=${NONE}    ${timeout}=60    ${poll_interval}=1    ${region}=${NONE}
    ${results}    ${meta}=    AwsLogs.Run Query And Wait
    ...    ${log_group}    ${query}    ${start_time}    ${end_time}    ${timeout}    ${poll_interval}    ${region}
    RETURN    ${results}    ${meta}

Start CloudWatch Insights Query
    [Documentation]    Start a CloudWatch Logs Insights query without waiting;
    ...    returns (queryId, raw start response).
    [Arguments]    ${log_group}    ${query}    ${start_time}=${NONE}    ${end_time}=${NONE}    ${region}=${NONE}
    ${qid}    ${resp}=    AwsLogs.Start Query    ${log_group}    ${query}    ${start_time}    ${end_time}    ${region}
    RETURN    ${qid}    ${resp}

Run Azure Log Query And Wait
    [Documentation]    Run a Log Analytics (Kusto) query and return (results, metadata).
    [Arguments]    ${workspace}    ${query}    ${timeout}=60
    ${results}    ${meta}=    AzureLogs.Run Query And Wait    ${workspace}    ${query}    ${timeout}
    RETURN    ${results}    ${meta}

Run GCP Log Query And Wait
    [Documentation]    Run a Cloud Logging filter query and return (results, metadata).
    [Arguments]    ${project}    ${filter}    ${timeout}=60    ${page_size}=100
    ${results}    ${meta}=    GcpLogs.Run Query And Wait    ${project}    ${filter}    ${timeout}    ${page_size}
    RETURN    ${results}    ${meta}

Get Violation Count
    [Documentation]    Count rows in CloudWatch Insights results (list of lists of
    ...    field dicts) where the given field equals '1'.
    ...
    ...    Uses a list comprehension rather than a generator expression:
    ...    generator expressions execute their inner ``for``/``if`` clauses
    ...    in a separate scope that Robot's ``$var`` substitution cannot
    ...    see once nested past the first ``for``, causing
    ...    "variable is used in a scope where it cannot be seen" at
    ...    runtime (this affected the original M-26-14 keyword this was
    ...    ported from too - it was never actually exercised against a
    ...    live Robot run until this package's smoke-test suite caught it;
    ...    see https://github.com/GSA-TTS/robotframework-compliance-kit/issues/13).
    [Arguments]    ${results}    ${flag_field}=violation
    ${count}=    Evaluate    sum([1 for row in $results for field in row if field['field'] == $flag_field and field['value'] == '1'])
    RETURN    ${count}
