from __future__ import annotations

import pytest

from gsa_compliance_robot.bod1801 import BOD1801Checks


class _StubResp:
    def __init__(self, status_code: int, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self.headers = headers or {}


@pytest.fixture
def checks():
    c = BOD1801Checks()
    c._resolve_txt = lambda name: []  # type: ignore[assignment]
    c._check_tls_and_hsts = lambda domain: []  # type: ignore[assignment]
    return c


def test_extract_domain_strips_scheme_path_port():
    assert BOD1801Checks._extract_domain("https://cfo.gov/foo?x=1") == "cfo.gov"
    assert BOD1801Checks._extract_domain("http://example.com:8080/") == "example.com"
    assert BOD1801Checks._extract_domain("") == ""
    assert BOD1801Checks().check_domain("") == []


def test_missing_spf_and_dmarc_are_reported(checks):
    findings = checks.check_domain("https://example.gov")
    features = {f["feature"] for f in findings}
    assert "BOD 18-01 SPF" in features
    assert "BOD 18-01 DMARC" in features


def test_soft_spf_and_quarantine_dmarc_flagged(checks):
    def fake_txt(name):
        if name == "example.gov":
            return ["other-txt", "v=spf1 ~all"]
        if name == "_dmarc.example.gov":
            return ["other-txt", "v=DMARC1; p=quarantine"]
        return []

    checks._resolve_txt = fake_txt  # type: ignore[assignment]
    findings = checks.check_domain("https://example.gov")
    assert len(findings) == 2
    assert all(f["type"] == "POLICY_VIOLATION" for f in findings)


def test_compliant_spf_and_dmarc(checks):
    def fake_txt(name):
        if name == "example.gov":
            return ["v=spf1 -all"]
        if name == "_dmarc.example.gov":
            return ["v=DMARC1; p=reject"]
        return []

    checks._resolve_txt = fake_txt  # type: ignore[assignment]
    assert checks.check_domain("https://example.gov") == []


def test_tls_weak_cipher_and_http_400_and_missing_hsts(monkeypatch):
    c = BOD1801Checks()
    c._resolve_txt = lambda name: (  # type: ignore[assignment]
        ["v=spf1 -all"]
        if name == "example.gov"
        else ["v=DMARC1; p=reject"]
        if name == "_dmarc.example.gov"
        else []
    )

    class FakeSSock:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def cipher(self):
            return ("ECDHE-RSA-3DES-EDE-CBC-SHA", "TLSv1.2", 168)

    class FakeContext:
        def wrap_socket(self, sock, server_hostname=None):
            return FakeSSock()

    class FakeSock:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(
        "gsa_compliance_robot.bod1801.ssl.create_default_context",
        lambda: FakeContext(),
    )
    monkeypatch.setattr(
        "gsa_compliance_robot.bod1801.socket.create_connection",
        lambda *a, **kw: FakeSock(),
    )
    monkeypatch.setattr(
        "gsa_compliance_robot.bod1801.requests.head",
        lambda url, timeout, allow_redirects: _StubResp(500, headers={}),
    )

    findings = c.check_domain("https://example.gov")
    features = {f["feature"] for f in findings}
    assert {"BOD 18-01 TLS", "BOD 18-01 HTTPS", "BOD 18-01 HSTS"} <= features


def test_probe_error_short_circuits_tls_findings(monkeypatch):
    c = BOD1801Checks()
    c._resolve_txt = lambda name: (  # type: ignore[assignment]
        ["v=spf1 -all"]
        if name == "example.gov"
        else ["v=DMARC1; p=reject"]
        if name == "_dmarc.example.gov"
        else []
    )

    def boom(*a, **kw):
        raise OSError("connection refused")

    monkeypatch.setattr("gsa_compliance_robot.bod1801.socket.create_connection", boom)
    findings = c.check_domain("https://example.gov")
    assert len(findings) == 1
    assert findings[0]["type"] == "PROBE_ERROR"
