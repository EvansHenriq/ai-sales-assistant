"""Agent orchestrator: coordinates a single conversation turn.

Phase 2 is a straight prompt→response turn with persistence. Tools (RAG search,
lead qualification, automation) are wired into this loop in later phases.
"""

from dataclasses import dataclass
from uuid import UUID

from app.agent.history import to_chat_messages
from app.agent.prompts import SALES_ASSISTANT_SYSTEM_PROMPT
from app.agent.types import LLMClient, LLMUsage
from app.db.models import MessageRole
from app.db.repositories import ConversationRepository
from app.rag.types import RetrievedChunk, Retriever

_RETRIEVAL_K = 4


def _format_context(chunks: list[RetrievedChunk]) -> str:
    blocks = [f"[Source: {chunk.source}]\n{chunk.content}" for chunk in chunks]
    return (
        "\n\n# Knowledge base\n"
        "Use the following retrieved context to ground your answer and cite the "
        "source titles. If it does not contain the answer, say so.\n\n" + "\n\n".join(blocks)
    )


@dataclass(frozen=True)
class TurnResult:
    reply: str
    usage: LLMUsage


class AgentOrchestrator:
    def __init__(
        self,
        *,
        llm: LLMClient,
        repo: ConversationRepository,
        retriever: Retriever | None = None,
        system_prompt: str = SALES_ASSISTANT_SYSTEM_PROMPT,
    ) -> None:
        self._llm = llm
        self._repo = repo
        self._retriever = retriever
        self._system_prompt = system_prompt

    async def handle_turn(self, *, conversation_id: UUID, user_message: str) -> TurnResult:
        await self._repo.add_message(
            conversation_id=conversation_id, role=MessageRole.user, content=user_message
        )

        system_prompt = self._system_prompt
        if self._retriever is not None:
            chunks = await self._retriever.search(user_message, k=_RETRIEVAL_K)
            if chunks:
                system_prompt = f"{system_prompt}{_format_context(chunks)}"

        history = await self._repo.list_messages(conversation_id)
        chat_messages = to_chat_messages(history)

        result = await self._llm.generate(system=system_prompt, messages=chat_messages)

        await self._repo.add_message(
            conversation_id=conversation_id,
            role=MessageRole.assistant,
            content=result.text,
            tokens=result.usage.total_tokens,
        )
        return TurnResult(reply=result.text, usage=result.usage)
