# gsa-compliance-robot

Reusable Robot Framework automations and audit-evidence helpers for GSA
security assessments and RPA tasks.

[![Test](https://github.com/GSA-TTS/robotframework-compliance-kit/actions/workflows/test.yml/badge.svg)](https://github.com/GSA-TTS/robotframework-compliance-kit/actions/workflows/test.yml)
[![Secret Scan](https://github.com/GSA-TTS/robotframework-compliance-kit/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/GSA-TTS/robotframework-compliance-kit/actions/workflows/secret-scan.yml)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)

> **Early-stage, public.** This package is usable today (install from this
> git repo; see [Installation](#installation)) but has not yet been adopted
> by its two intended first consumers (`M-26-14`, `gsa-pages`) and has not
> been published to PyPI. See the [open issues](https://github.com/GSA-TTS/robotframework-compliance-kit/issues)
> for the active hardening/migration roadmap — contributions and early
> feedback are welcome.

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
| `gsa_compliance_robot.browser_recording` | Redacted operator-action recorder for RF Browser exploration | gsa-pages `scripts/testing/browser_recording.py` + `browser_recording.resource` |
| `gsa_compliance_robot.reporting` | Compliance artifact/report/dashboard generation | gsa-pages `common.resource` + `reporting.resource` |
| `gsa_compliance_robot.allure_helpers` | Allure attachment keywords | gsa-pages `allure.resource` |
| `gsa_compliance_robot.bod1801` | DHS BOD 18-01 SPF, DMARC, TLS 1.2+, HTTPS, and HSTS checks | gsa-pages `BOD1801Checks.py` |
| `gsa_compliance_robot.vulnerability_timeline` | GSA vulnerability remediation SLA timeline tracking | gsa-pages `VulnerabilityTimeline.py` |
| `gsa_compliance_robot.evidence_manifest` | Evidence run provenance and SHA-256 manifest writer | gsa-pages `EvidenceManifest.py` |
| `gsa_compliance_robot.github` | Shared GitHub REST/GraphQL client + repository URL normalizer | gsa-pages `scripts/lib/github_client.py` + `RepoUrlNormalizer.py` |
| `gsa_compliance_robot.cloudgov` | **Unified** cloud.gov API/CLI client (token, `cf` CLI auth) | Merged from M-26-14 `CloudGovAPI.resource`/`CloudGovCLI.resource`/`CloudGovHelpers.py` **and** gsa-pages `cloudgov_auth.resource`/`cloudgov_api.resource` |
| `gsa_compliance_robot.cloudlogs` | AWS CloudWatch Insights / Azure Log Analytics / GCP Cloud Logging adapters behind one interface | M-26-14 `lib/aws_insights.py`, `azure_monitor.py`, `gcp_logging.py` |

Each Python module has a matching `.resource` file under
`src/gsa_compliance_robot/resources/` exposing the same functionality as
Robot Framework keywords.

## Installation

Not yet published to PyPI (see [#7](https://github.com/GSA-TTS/robotframework-compliance-kit/issues/7)).
Install directly from this repo for now:

```bash
pip install "gsa-compliance-robot @ git+https://github.com/GSA-TTS/robotframework-compliance-kit.git@main"
# or pin to a tag once releases start:
pip install "gsa-compliance-robot @ git+https://github.com/GSA-TTS/robotframework-compliance-kit.git@v0.1.0"

# optional extras:
pip install "gsa-compliance-robot[browser] @ git+https://github.com/GSA-TTS/robotframework-compliance-kit.git@main"
pip install "gsa-compliance-robot[allure] @ git+https://github.com/GSA-TTS/robotframework-compliance-kit.git@main"
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

Consumer repositories can vendor this repo as a pinned git submodule (e.g.,
`vendor/robotframework-compliance-kit`) and/or sync the `.resource` files
with a SHA-256 lockfile using `gsa-robot-vendor`:

```bash
# Sync .resource files and write vendor.lock.json
gsa-robot-vendor sync --dest tests/resources/vendor

# Verify zero drift in CI
gsa-robot-vendor check --dest tests/resources/vendor
```

A reusable GitHub Actions workflow (`.github/workflows/vendor-drift-check.yml`)
is also provided for `workflow_call` consumers.

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
