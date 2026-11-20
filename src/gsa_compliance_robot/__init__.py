"""GSA Compliance Robot — reusable Robot Framework automations and
audit-evidence helpers for GSA security assessments and RPA tasks.

See the package README for usage. Submodules:
  - env                    : .env loading, secret masking
  - redaction              : Robot listener masking secrets in output.xml/log.html
  - api_common             : HTTP header/response helpers
  - browser_session        : Playwright/Browser lifecycle keywords
  - browser_recording      : Redacted operator-action recorder for RF Browser
  - reporting              : compliance artifact/report/dashboard generation
  - allure_helpers         : Allure attachment keywords
  - bod1801                : DHS BOD 18-01 SPF/DMARC/TLS/HTTPS/HSTS posture checks
  - vulnerability_timeline : GSA vulnerability remediation SLA timeline tracking
  - evidence_manifest      : Evidence run provenance and SHA-256 manifest writer
  - github                 : GitHub REST/GraphQL client + repo URL normalizer
  - cloudgov               : unified cloud.gov API/CLI client
  - cloudlogs              : AWS/Azure/GCP log-query client adapters
  - vendor_sync            : CLI (`gsa-robot-vendor`) for syncing/checking .resource files
"""

__version__ = "0.2.0"
