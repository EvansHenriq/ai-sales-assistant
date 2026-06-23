"""BANT lead-qualification schema (structured output target).

Kept simple/strict-mode friendly for OpenAI structured outputs: enums and a
plain integer score (range is enforced in the prompt and validated here).
"""

from enum import StrEnum

from pydantic import BaseModel, field_validator


class BANTLevel(StrEnum):
    unknown = "unknown"
    low = "low"
    medium = "medium"
    high = "high"


class LeadStage(StrEnum):
    cold = "cold"
    warm = "warm"
    hot = "hot"


class LeadQualificationResult(BaseModel):
    budget: BANTLevel
    authority: BANTLevel
    need: BANTLevel
    timeline: BANTLevel
    score: int  # overall 0-100 qualification score
    stage: LeadStage
    rationale: str

    @field_validator("score")
    @classmethod
    def _clamp_score(cls, value: int) -> int:
        return max(0, min(100, value))
