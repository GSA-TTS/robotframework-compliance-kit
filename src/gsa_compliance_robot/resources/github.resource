*** Settings ***
Documentation       GitHub repository URL normalization and API URL validation keywords.
...
...                 Backed by gsa_compliance_robot.github (`RepoUrlNormalizer`
...                 and `validate_github_api_url`).
Library             gsa_compliance_robot.github.url_normalizer.RepoUrlNormalizer    AS    GsaRepoNormalizer
Library             gsa_compliance_robot.github.client    AS    GsaGitHubClient


*** Keywords ***
Normalize Repository URL
    [Documentation]    Canonicalize a GitHub repository cell to `github.com/<Org>/<Repo>`.
    [Arguments]    ${repo_url}
    ${normalized}=    GsaRepoNormalizer.Normalize Repo Url    ${repo_url}
    RETURN    ${normalized}

Validate GitHub API URL
    [Documentation]    Verify that ${url} targets `https://api.github.com` and return it.
    [Arguments]    ${url}
    ${validated}=    GsaGitHubClient.Validate Github Api Url    ${url}
    RETURN    ${validated}
