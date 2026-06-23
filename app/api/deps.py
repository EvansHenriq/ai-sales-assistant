"""Shared FastAPI dependencies: database session and API-key authentication."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.openai_client import get_llm_client
from app.agent.types import LLMClient
from app.core.security import hash_api_key
from app.db.models import ApiKey
from app.db.session import get_session

DbSession = Annotated[AsyncSession, Depends(get_session)]
LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]


async def require_api_key(
    session: DbSession,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> ApiKey:
    """Authenticate the request by its ``X-API-Key`` header.

    The missing-header path returns 401 without touching the database.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    result = await session.execute(
        select(ApiKey).where(
            ApiKey.key_hash == hash_api_key(x_api_key),
            ApiKey.revoked_at.is_(None),
        )
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


RequireApiKey = Annotated[ApiKey, Depends(require_api_key)]
