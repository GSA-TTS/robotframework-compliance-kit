"""BOD 18-01 network posture checks (SPF, DMARC, TLS, HSTS).

Extracted from gsa-pages (tests/libraries/BOD1801Checks.py) so any GSA
compliance or ATU Robot Framework suite can verify DHS BOD 18-01 domain
posture without duplicating DNS/TLS probe logic. Every check returns a
plain dict (`{feature, type, expected, actual}`).

Behavior notes:
- All network calls have short timeouts and swallow their own errors —
  a failing DNS or TLS probe is reported as a finding, not an exception.
- `check_domain` is the single Robot-facing entry point; it fans out to
  DNS + TLS and returns the union of findings.
- BOD 18-01 baseline probes performed:
    - SPF: `v=spf1 -all` (hard fail)
    - DMARC: `p=reject`
    - TLS 1.2+ handshake succeeds and negotiated cipher is not 3DES/RC4/DES
      (note: observes the negotiated cipher on a single TLS 1.2+ connection;
      does not enumerate all server-supported cipher suites)
    - HTTPS endpoint responds (< 400) with a `Strict-Transport-Security` header
- See https://cyber.dhs.gov/bod/18-01/ for the canonical policy text.
"""

from __future__ import annotations

import re
import socket
import ssl
from typing import Any

try:
    import dns.exception
    import dns.resolver

    _DNSPYTHON = True
except ImportError:  # pragma: no cover - optional runtime dependency
    _DNSPYTHON = False

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

__all__ = ["BOD1801Checks"]


class BOD1801Checks:
    """Robot library that emits BOD 18-01 discrepancies for a given site URL."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, dns_timeout: float = 5.0, http_timeout: float = 10.0):
        self._dns_timeout = dns_timeout
        self._http_timeout = http_timeout
        self._resolver = None
        if _DNSPYTHON:
            self._resolver = dns.resolver.Resolver()
            self._resolver.timeout = dns_timeout
            self._resolver.lifetime = dns_timeout

    def check_domain(self, site_url: str) -> list[dict[str, Any]]:
        """Return a list of BOD 18-01 discrepancy dicts for `site_url`.

        Each finding has the shape ``{feature, type, expected, actual}``.
        Empty list means the domain is BOD 18-01 compliant for the checks run.
        """
        domain = self._extract_domain(site_url)
        if not domain:
            return []
        findings: list[dict[str, Any]] = []
        findings.extend(self._check_spf(domain))
        findings.extend(self._check_dmarc(domain))
        findings.extend(self._check_tls_and_hsts(domain))
        return findings

    @staticmethod
    def _extract_domain(url: str) -> str:
        if not url:
            return ""
        cleaned = re.sub(r"^https?://", "", url.strip())
        cleaned = cleaned.split("/", 1)[0]
        cleaned = cleaned.split(":", 1)[0]
        return cleaned

    def _resolve_txt(self, name: str) -> list[str]:
        if not self._resolver:
            return []
        try:
            answers = self._resolver.resolve(name, "TXT")
        except (
            dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
        ):
            return []
        return [rdata.to_text().strip('"') for rdata in answers]

    def _check_spf(self, domain: str) -> list[dict[str, Any]]:
        for txt in self._resolve_txt(domain):
            if not txt.startswith("v=spf1"):
                continue
            if txt.strip() == "v=spf1 -all":
                return []
            return [
                {
                    "feature": "BOD 18-01 SPF",
                    "type": "POLICY_VIOLATION",
                    "expected": "v=spf1 -all",
                    "actual": txt,
                }
            ]
        return [
            {
                "feature": "BOD 18-01 SPF",
                "type": "MISSING_CONFIGURATION",
                "expected": "v=spf1 -all",
                "actual": "no SPF record",
            }
        ]

    def _check_dmarc(self, domain: str) -> list[dict[str, Any]]:
        for txt in self._resolve_txt(f"_dmarc.{domain}"):
            if "v=DMARC1" not in txt:
                continue
            if "p=reject" in txt:
                return []
            return [
                {
                    "feature": "BOD 18-01 DMARC",
                    "type": "POLICY_VIOLATION",
                    "expected": "p=reject",
                    "actual": txt,
                }
            ]
        return [
            {
                "feature": "BOD 18-01 DMARC",
                "type": "MISSING_CONFIGURATION",
                "expected": "DMARC record with p=reject",
                "actual": "no DMARC record",
            }
        ]

    def _check_tls_and_hsts(self, domain: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        weak_ciphers = ("3DES", "RC4", "DES")

        try:
            context = ssl.create_default_context()
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            with socket.create_connection(
                (domain, 443), timeout=self._http_timeout
            ) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cipher = ssock.cipher()
                    if cipher:
                        cipher_name = (
                            cipher[0] if isinstance(cipher, tuple) else str(cipher)
                        )
                        if any(w in cipher_name.upper() for w in weak_ciphers):
                            findings.append(
                                {
                                    "feature": "BOD 18-01 TLS",
                                    "type": "POLICY_VIOLATION",
                                    "expected": "no 3DES/RC4/DES ciphers",
                                    "actual": cipher_name,
                                }
                            )
        except (TimeoutError, OSError, ssl.SSLError) as exc:
            findings.append(
                {
                    "feature": "BOD 18-01 TLS",
                    "type": "PROBE_ERROR",
                    "expected": "TLS 1.2+ handshake succeeds",
                    "actual": f"{type(exc).__name__}: {exc}",
                }
            )
            return findings

        if requests is None:  # pragma: no cover
            return findings

        try:
            resp = requests.head(
                f"https://{domain}",
                timeout=self._http_timeout,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            findings.append(
                {
                    "feature": "BOD 18-01 HTTPS",
                    "type": "PROBE_ERROR",
                    "expected": "HTTPS reachable",
                    "actual": f"{type(exc).__name__}: {exc}",
                }
            )
            return findings

        if resp.status_code >= 400:
            findings.append(
                {
                    "feature": "BOD 18-01 HTTPS",
                    "type": "POLICY_VIOLATION",
                    "expected": "site responds on HTTPS",
                    "actual": f"HTTP {resp.status_code}",
                }
            )

        hsts_header = resp.headers.get("strict-transport-security")
        if not hsts_header:
            findings.append(
                {
                    "feature": "BOD 18-01 HSTS",
                    "type": "MISSING_CONFIGURATION",
                    "expected": "Strict-Transport-Security header present",
                    "actual": "no HSTS header",
                }
            )

        return findings
