"""Create an API key and print the raw value once (it is never shown again).

Run: uv run python scripts/create_api_key.py "client name"
Requires a DATABASE_URL.
"""

import asyncio
import sys

from app.core.security import generate_api_key, hash_api_key
from app.db.models import ApiKey
from app.db.session import get_sessionmaker


async def main(name: str) -> None:
    raw_key = generate_api_key()
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        session.add(ApiKey(name=name, key_hash=hash_api_key(raw_key)))
        await session.commit()
    print("API key created. Store it now - it will not be shown again:")
    print(raw_key)


if __name__ == "__main__":
    client_name = sys.argv[1] if len(sys.argv) > 1 else "demo"
    asyncio.run(main(client_name))
