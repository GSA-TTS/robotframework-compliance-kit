# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.0] - 2026-11-20

### Added

- Implemented `gsa-robot-vendor` CLI (`sync` and `check` / `--check` modes) in `gsa_compliance_robot.vendor_sync` with `# VENDORED from gsa-compliance-robot` banners, `vendor.lock.json` SHA-256 digests, and reusable `.github/workflows/vendor-drift-check.yml` workflow (closes #10).
- Extracted additional reusable compliance foundations from `GSA-TTS/gsa-pages` (with matching `.resource` files and unit + Robot smoke tests):
  - `gsa_compliance_robot.bod1801` + `resources/bod1801.resource` — DHS BOD 18-01 SPF, DMARC, TLS 1.2+, HTTPS, and HSTS checks.
  - `gsa_compliance_robot.vulnerability_timeline` + `resources/vulnerability_timeline.resource` — GSA vulnerability remediation SLA timeline tracking (15/30/90/180-day deadlines) and Markdown report formatting.
  - `gsa_compliance_robot.evidence_manifest` + `resources/evidence_manifest.resource` — Evidence run provenance and SHA-256 file/directory manifest writer.
  - `gsa_compliance_robot.browser_recording` + `resources/browser_recording.resource` — Redacted DOM operator-action recorder for RF Browser exploration.
  - `gsa_compliance_robot.github` (`client.py`, `url_normalizer.py`) + `resources/github.resource` — Shared GitHub REST/GraphQL client with SSRF host validation, exponential backoff / `Retry-After`, pagination, `RepoIssuesClient`, and `RepoUrlNormalizer`.
- Full test coverage for previously-gapped modules (closes #6):
  - `tests/test_browser_session.py` — mocks `BuiltIn().get_library_instance('Browser')` to unit test lifecycle keywords without a live Playwright session.
  - `tests/test_allure_helpers.py` — same pattern for `AllureLibrary`.
  - `tests/test_cloudlogs_azure.py`, `tests/test_cloudlogs_gcp.py` — mock the Azure/GCP SDK clients, following the existing `test_cloudlogs_aws.py` pattern.
  - `tests/test_vendor_sync.py` — pins down the current placeholder CLI's help/error UX as a baseline for the future real implementation (#10).
  - Additional `cloudlogs/aws.py` edge-case tests (statistics logging, expired-token retry during polling, non-expired-token error path, timeout-exhausted fallback).
  - Overall coverage: 65% → 95%.
- Security/governance infrastructure (closes #2, #3, #5, #8):
  - `.gitleaks.toml` + `.github/workflows/secret-scan.yml` — CI secret scanning (gitleaks) on every push/PR with full git history.
  - `.github/dependabot.yml` — weekly pip + github-actions dependency update PRs.
  - `.github/workflows/codeql.yml` — weekly + push/PR CodeQL analysis for Python.
  - `.github/workflows/dependency-audit.yml` — pip-audit against the fully-resolved lockfile (all extras).
  - `.github/CODEOWNERS` — required review on security-critical paths.
  - `CODE_OF_CONDUCT.md` — adapted from `GSA-TTS/agentic-coding-patterns`.
  - Branch protection on `main`: required status checks (pytest, robocop, robotcode-analyze, gitleaks, pip-audit, CodeQL), 1 required approving + CODEOWNERS review, no force-push/deletion.

### Changed

- README/CONTRIBUTING/SECURITY updated to reflect public (not internal-bootstrap) status.

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
