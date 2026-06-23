"""Heuristic prompt-injection detection.

A fast, deterministic first line of defense over known injection phrasings. It
complements (does not replace) the structural defense of always treating user
content as data. A model-based classifier could be layered on top.
"""

import re
from dataclasses import dataclass

# Targeted patterns kept deliberately specific to limit false positives.
_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"ignore (?:all |the |your |any )?(?:previous|above|prior|earlier) "
        r"(?:instructions|prompts?|messages?)",
        r"disregard (?:all |the |your |any )?(?:previous|above|prior|earlier)",
        r"forget (?:everything|all|your|the) (?:instructions|rules|prompt)",
        r"you are now (?:a |an )?",
        r"(?:reveal|show|print|repeat|expose) (?:me )?(?:your )?(?:the )?"
        r"(?:system )?(?:prompt|instructions)",
        r"what (?:is|are) your (?:system )?(?:prompt|instructions)",
        r"developer mode",
        r"\bjailbreak\b",
        r"override (?:your )?(?:instructions|rules|safety|guardrails)",
        r"do anything now|\bDAN\b",
    )
)


@dataclass(frozen=True)
class InjectionVerdict:
    is_injection: bool
    reasons: list[str]


def detect_injection(text: str) -> InjectionVerdict:
    reasons = [pattern.pattern for pattern in _PATTERNS if pattern.search(text)]
    return InjectionVerdict(is_injection=bool(reasons), reasons=reasons)
