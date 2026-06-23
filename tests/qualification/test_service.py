from app.agent.types import ChatMessage
from app.qualification.models import BANTLevel, LeadQualificationResult, LeadStage
from app.qualification.service import QualificationService
from tests.fakes import FakeLLMClient


async def test_qualify_returns_parsed_result_and_passes_schema() -> None:
    expected = LeadQualificationResult(
        budget=BANTLevel.high,
        authority=BANTLevel.medium,
        need=BANTLevel.high,
        timeline=BANTLevel.low,
        score=72,
        stage=LeadStage.hot,
        rationale="Strong need and budget.",
    )
    fake = FakeLLMClient(parsed=expected)
    service = QualificationService(fake, model="test-model")

    result, usage = await service.qualify([ChatMessage(role="user", content="we have budget")])

    assert result == expected
    assert usage.total_tokens == 12
    assert fake.parse_calls[0]["schema"] is LeadQualificationResult
    assert fake.parse_calls[0]["model"] == "test-model"


def test_score_is_clamped_to_0_100() -> None:
    result = LeadQualificationResult(
        budget=BANTLevel.low,
        authority=BANTLevel.low,
        need=BANTLevel.low,
        timeline=BANTLevel.low,
        score=150,
        stage=LeadStage.cold,
        rationale="x",
    )
    assert result.score == 100
