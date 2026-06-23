"""Regex-based PII detection and redaction.

Used to produce a masked copy of user content for logs/analytics so raw PII is
not scattered through logs. Raw contact details live only in the ``leads`` table.
This is a pragmatic baseline (not exhaustive); a library like Presidio could be
layered on for broader coverage.
"""

import re
from dataclasses import dataclass

# Ordered: more specific patterns first so they win over the looser phone match.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("CPF", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("PHONE", re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d(?!\w)")),
)


@dataclass(frozen=True)
class RedactionResult:
    text: str
    found: list[str]


def redact_pii(text: str) -> RedactionResult:
    redacted = text
    found: list[str] = []
    for label, pattern in _PATTERNS:
        if pattern.search(redacted):
            found.append(label)
            redacted = pattern.sub(f"[REDACTED_{label}]", redacted)
    return RedactionResult(text=redacted, found=found)
