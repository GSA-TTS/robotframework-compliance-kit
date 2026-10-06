"""Robot Framework listener that redacts secret values from log messages and
keyword arguments.

Extracted from gsa-pages (tests/libraries/RedactionListener.py) and
generalized: the GitHub-token-specific patterns remain as a sensible default
set, but callers can register additional regex patterns via
`RedactionListener.register_pattern` for domain-specific secret shapes
(API keys, session tokens, etc.) without forking this module.

Attaches at listener API v3 (Robot Framework 7.x). Scans messages, keyword
arguments, and return values for known-sensitive substrings and replaces
them with a masked placeholder before Robot writes them to output.xml,
log.html, or the console.

Usage
-----
    robot --listener gsa_compliance_robot.redaction.RedactionListener ...

Or via the packaged resource file:
    Library    gsa_compliance_robot.redaction.RedactionListener

Design
------
Robot's default behaviour is to auto-log every keyword argument to
output.xml. That means a token passed as `Bearer ${token}` will land in the
XML in cleartext even though a test log line uses a masked helper. This
listener intercepts the message _before_ it is written and rewrites any
occurrence of a known token pattern, plus explicit values registered via
`Register Secret`.

Security note
-------------
This listener is a defence-in-depth measure. It does NOT replace the
operational requirement to (a) never hard-code tokens in source, (b) rotate
any token that touches disk, and (c) keep test artifacts out of version
control.
"""

from __future__ import annotations

import logging
import re
from typing import Any, ClassVar

_MASK = "***REDACTED***"
_logger = logging.getLogger(__name__)


def _log_scrub_failure(exc: BaseException) -> None:
    """Record a scrub failure without letting it propagate into Robot."""
    _logger.debug("RedactionListener scrub failed: %s", exc, exc_info=exc)


_DEFAULT_PATTERNS: tuple[re.Pattern[str], ...] = (
    # GitHub classic PATs
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    # GitHub App user-to-server tokens
    re.compile(r"ghu_[A-Za-z0-9]{20,}"),
    # GitHub App server-to-server tokens
    re.compile(r"ghs_[A-Za-z0-9]{20,}"),
    # GitHub App refresh tokens
    re.compile(r"ghr_[A-Za-z0-9]{20,}"),
    # Fine-grained PATs
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    # JWT: three base64url segments joined by "."
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    # Bearer header with an opaque value (any non-whitespace, at least 20 chars).
    re.compile(r"(?i)(Bearer\s+)([A-Za-z0-9_.\-+/=]{20,})"),
    # AWS access key IDs / secret-looking long base64 session tokens.
    re.compile(r"AKIA[0-9A-Z]{16}"),
)


class RedactionListener:
    """Robot Framework listener v3 that masks secrets in messages and keyword data.

    Doubles as a Robot library: importing this module via
    ``Library    gsa_compliance_robot.redaction.RedactionListener`` exposes
    the ``Register Secret`` and ``Register Pattern`` keywords. The listener
    behaviour activates only when the module is also passed via
    ``--listener``.
    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LISTENER_API_VERSION = 3

    # Additional literal values / patterns registered at runtime. Shared
    # across listener instances so Register Secret/Pattern work regardless
    # of how Robot instantiates the listener.
    _extra_literals: ClassVar[set[str]] = set()
    _extra_patterns: ClassVar[list[re.Pattern[str]]] = []

    def __init__(self, *_args: str) -> None:
        # Accept but ignore constructor args so users can wire in overrides
        # without breaking if none are supplied.
        pass

    # ---- listener v3 hooks ------------------------------------------------

    def log_message(self, message: Any) -> None:  # pragma: no cover - RF hook
        self._safe_scrub_message(message)

    def message(self, message: Any) -> None:  # pragma: no cover - RF hook
        self._safe_scrub_message(message)

    def start_keyword(self, data: Any, result: Any) -> None:  # pragma: no cover
        try:
            if getattr(data, "args", None):
                data.args = [self._scrub(str(a)) for a in data.args]
        except Exception as exc:
            _log_scrub_failure(exc)

    def end_keyword(self, data: Any, result: Any) -> None:  # pragma: no cover
        try:
            if getattr(result, "message", None):
                result.message = self._scrub(result.message)
        except Exception as exc:
            _log_scrub_failure(exc)

    def _safe_scrub_message(self, message: Any) -> None:
        try:
            message.message = self._scrub(message.message)
        except Exception as exc:
            _log_scrub_failure(exc)

    # ---- Robot Framework keyword interface --------------------------------

    def register_secret(self, value: str) -> None:
        """Robot keyword: register a runtime secret so it is masked in artifacts.

        The listener strips any occurrence of ``value`` from log messages,
        keyword arguments, and return values before Robot writes them to
        output.xml. No-op when ``value`` is empty or shorter than 8
        characters.
        """
        if value and len(value) >= 8:
            type(self)._extra_literals.add(value)

    def register_pattern(self, pattern: str) -> None:
        """Robot keyword: register an additional regex pattern to mask.

        Use this for domain-specific secret shapes not covered by the
        built-in GitHub/JWT/Bearer/AWS patterns (e.g., an internal API key
        format). The pattern is compiled once and kept for the life of the
        process.
        """
        compiled = re.compile(pattern)
        if compiled not in type(self)._extra_patterns:
            type(self)._extra_patterns.append(compiled)

    # ---- internal helpers -------------------------------------------------

    @classmethod
    def _scrub(cls, text: str) -> str:
        if not text or not isinstance(text, str):
            return text
        scrubbed = text
        for pattern in (*_DEFAULT_PATTERNS, *cls._extra_patterns):
            if pattern.groups >= 2:
                # Bearer-style pattern — preserve group 1, mask group 2.
                scrubbed = pattern.sub(r"\1" + _MASK, scrubbed)
            else:
                scrubbed = pattern.sub(_MASK, scrubbed)
        for literal in cls._extra_literals:
            if literal in scrubbed:
                scrubbed = scrubbed.replace(literal, _MASK)
        return scrubbed


# Module-level convenience wrapper — allows non-Robot callers (unit tests,
# other Python scripts) to register a secret without instantiating the class.
def register_secret(value: str) -> None:
    """Register an additional literal string to be masked in all future output."""
    if value and len(value) >= 8:
        RedactionListener._extra_literals.add(value)
