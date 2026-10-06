# gsa-compliance-robot

Reusable Robot Framework automations and audit-evidence helpers for GSA
security assessments and RPA tasks.

> **Status: internal bootstrap.** This repository is not yet public. See the
> issue tracker for the pre-release checklist before any public announcement
> or external promotion.

## Why this exists

Two GSA-TTS repositories — [`M-26-14`](https://github.com/GSA-TTS/M-26-14)
(cloud log/audit assessment automation) and
[`gsa-pages`](https://github.com/GSA-TTS/gsa-pages) (SSP/OSCAL + ATU/GitHub
compliance automation) — independently built overlapping Robot Framework
infrastructure: environment/secret handling, Playwright browser session
management, compliance artifact/report generation, and (most notably) two
separate, non-interoperable cloud.gov API/CLI clients.

This repo extracts the generic, non-domain-specific pieces into one
versioned Python package so future consumers (compliance, audit, and RPA
Robot Framework suites across GSA) can depend on a single, tested
implementation instead of re-authoring or forking it.

## What's here

| Module | Purpose | Extracted from |
|---|---|---|
| `gsa_compliance_robot.env` | `.env` loading, secret masking | gsa-pages `environment.resource`/`auth.resource` (previously duplicated in-repo) |
| `gsa_compliance_robot.redaction` | Robot listener masking secrets in `output.xml`/`log.html` | gsa-pages `RedactionListener.py` |
| `gsa_compliance_robot.api_common` | HTTP header builders, response validation | gsa-pages `api_common.resource` |
| `gsa_compliance_robot.browser_session` | Playwright/Browser lifecycle keywords | gsa-pages `browser.resource` |
| `gsa_compliance_robot.reporting` | Compliance artifact/report/dashboard generation | gsa-pages `common.resource` + `reporting.resource` |
| `gsa_compliance_robot.allure_helpers` | Allure attachment keywords | gsa-pages `allure.resource` |
| `gsa_compliance_robot.cloudgov` | **Unified** cloud.gov API/CLI client (token, `cf` CLI auth) | Merged from M-26-14 `CloudGovAPI.resource`/`CloudGovCLI.resource`/`CloudGovHelpers.py` **and** gsa-pages `cloudgov_auth.resource`/`cloudgov_api.resource` |
| `gsa_compliance_robot.cloudlogs` | AWS CloudWatch Insights / Azure Log Analytics / GCP Cloud Logging adapters behind one interface | M-26-14 `lib/aws_insights.py`, `azure_monitor.py`, `gcp_logging.py` |

Each Python module has a matching `.resource` file under
`src/gsa_compliance_robot/resources/` exposing the same functionality as
Robot Framework keywords.

## Installation

```bash
pip install gsa-compliance-robot
# or, for Browser-library keywords:
pip install "gsa-compliance-robot[browser]"
# or, for Allure keywords:
pip install "gsa-compliance-robot[allure]"
```

## Usage in a Robot suite

```robot
*** Settings ***
Resource    gsa_compliance_robot/resources/env.resource
Resource    gsa_compliance_robot/resources/cloudgov.resource

*** Test Cases ***
Fetch Audit Events
    Load Environment Variables
    ${token}=    Authenticate With Cloud Gov Token    existing_token=%{CF_OAUTH_TOKEN}
    ${guid}=    Get Cloud Gov Organization GUID    my-org
    ${events}=    Query Cloud Gov Audit Events    ${guid}
```

## Vendoring into a consumer repo

This is **out of scope for the initial bootstrap**. The intended model —
install the Python package normally, but vendor (copy) the `.resource`
files into each consumer repo at a pinned version with a CI drift check —
is tracked as a separate issue. For now, resolve `.resource` file paths via
your installed package location or `importlib.resources`.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run robocop check src/
```

## License

CC0 1.0 Universal Public Domain Dedication — see [LICENSE](./LICENSE). As a
work of the United States Government, this project is in the public domain
within the United States.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Security

See [SECURITY.md](./SECURITY.md). Do not report vulnerabilities in public
GitHub issues.
