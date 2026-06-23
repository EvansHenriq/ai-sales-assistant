"""Map persisted messages to provider-agnostic chat messages."""

from app.agent.types import ChatMessage, Role
from app.db.models import Message, MessageRole


def _to_chat_role(role: MessageRole) -> Role | None:
    if role == MessageRole.user:
        return "user"
    if role == MessageRole.assistant:
        return "assistant"
    return None


def to_chat_messages(messages: list[Message]) -> list[ChatMessage]:
    chat_messages: list[ChatMessage] = []
    for message in messages:
        chat_role = _to_chat_role(message.role)
        if chat_role is not None:
            chat_messages.append(ChatMessage(role=chat_role, content=message.content))
    return chat_messages
