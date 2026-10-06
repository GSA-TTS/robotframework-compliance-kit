# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2026-10-06

### Added

- Initial bootstrap extraction from `GSA-TTS/M-26-14` and `GSA-TTS/gsa-pages`:
  - `env` — `.env` loading and secret masking (from gsa-pages `environment.resource`/`auth.resource`, which had duplicated this logic in-repo).
  - `redaction` — Robot listener masking secrets in `output.xml`/`log.html` (from gsa-pages `RedactionListener.py`), generalized with a `register_pattern` keyword for non-GitHub secret shapes.
  - `api_common` — HTTP header builders and response validation (from gsa-pages `api_common.resource`).
  - `browser_session` — Playwright/Browser lifecycle keywords (from gsa-pages `browser.resource`).
  - `reporting` — compliance artifact/report/dashboard generation (from gsa-pages `common.resource` + `reporting.resource`).
  - `allure_helpers` — Allure attachment keywords (from gsa-pages `allure.resource`).
  - `cloudgov` — **unified** cloud.gov API/CLI client merging M-26-14's `CloudGovAPI.resource`/`CloudGovCLI.resource`/`CloudGovHelpers.py` with gsa-pages's `cloudgov_auth.resource`/`cloudgov_api.resource` (the latter was mock-data-only; the unified client always calls the real API/CLI).
  - `cloudlogs` — AWS CloudWatch Insights / Azure Log Analytics / GCP Cloud Logging adapters behind one `CloudLogQueryClient` interface (from M-26-14 `lib/aws_insights.py`, `azure_monitor.py`, `gcp_logging.py`).
  - Matching `.resource` files for every module under `src/gsa_compliance_robot/resources/`.
  - Shared `robocop.toml` baseline (intersection of M-26-14's and gsa-pages's independently-converged ignore lists).
  - pytest unit test suite (83 tests) covering all Python modules except `allure_helpers`/`browser_session` (require live `AllureLibrary`/`Browser` instances — see tracked follow-up issue) and `vendor_sync` (placeholder, not yet implemented).
  - CI workflow: pytest+coverage, robocop, robotcode analyze.

### Notes

- This is an **internal bootstrap** release. The repository is not yet public — see the issue tracker for the pre-public-release checklist.
- The `gsa-robot-vendor` CLI entry point is a placeholder; the vendor-sync workflow (copy pinned `.resource` files into consumer repos with a lockfile + CI drift check) is deferred to a follow-up issue.
- Consumer repos (`M-26-14`, `gsa-pages`) have **not yet been migrated** to depend on this package — that is tracked as separate follow-up issues per repo.
