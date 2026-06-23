"""Agent orchestrator: coordinates a single conversation turn.

Phase 2 is a straight prompt→response turn with persistence. Tools (RAG search,
lead qualification, automation) are wired into this loop in later phases.
"""

from dataclasses import dataclass
from uuid import UUID

from app.agent.prompts import SALES_ASSISTANT_SYSTEM_PROMPT
from app.agent.types import ChatMessage, LLMClient, LLMUsage, Role
from app.db.models import MessageRole
from app.db.repositories import ConversationRepository


def _to_chat_role(role: MessageRole) -> Role | None:
    if role == MessageRole.user:
        return "user"
    if role == MessageRole.assistant:
        return "assistant"
    return None


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
        system_prompt: str = SALES_ASSISTANT_SYSTEM_PROMPT,
    ) -> None:
        self._llm = llm
        self._repo = repo
        self._system_prompt = system_prompt

    async def handle_turn(self, *, conversation_id: UUID, user_message: str) -> TurnResult:
        await self._repo.add_message(
            conversation_id=conversation_id, role=MessageRole.user, content=user_message
        )

        history = await self._repo.list_messages(conversation_id)
        chat_messages: list[ChatMessage] = []
        for message in history:
            chat_role = _to_chat_role(message.role)
            if chat_role is not None:
                chat_messages.append(ChatMessage(role=chat_role, content=message.content))

        result = await self._llm.generate(system=self._system_prompt, messages=chat_messages)

        await self._repo.add_message(
            conversation_id=conversation_id,
            role=MessageRole.assistant,
            content=result.text,
            tokens=result.usage.total_tokens,
        )
        return TurnResult(reply=result.text, usage=result.usage)
