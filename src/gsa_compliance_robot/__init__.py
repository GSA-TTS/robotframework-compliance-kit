"""GSA Compliance Robot — reusable Robot Framework automations and
audit-evidence helpers for GSA security assessments and RPA tasks.

See the package README for usage. Submodules:
  - env            : .env loading, secret masking
  - redaction      : Robot listener masking secrets in output.xml/log.html
  - api_common     : HTTP header/response helpers
  - browser_session: Playwright/Browser lifecycle keywords
  - reporting      : compliance artifact/report/dashboard generation
  - allure_helpers : Allure attachment keywords
  - cloudgov       : unified cloud.gov API/CLI client
  - cloudlogs      : AWS/Azure/GCP log-query client adapters
"""

__version__ = "0.1.0"
