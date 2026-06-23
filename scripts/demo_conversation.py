"""Drive a full sales conversation against a running API instance.

Start the stack (docker compose up), seed the knowledge base, create an API key,
then run:
  uv run python scripts/demo_conversation.py --api-key <KEY>
"""

import argparse
import asyncio

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"

_MESSAGES = [
    "Hi! What does FlowMetrics do, and how much is the Growth plan?",
    "We're a 120-person SaaS, have budget approved, and want to go live next month.",
]


async def main(api_key: str, base_url: str) -> None:
    headers = {"X-API-Key": api_key}
    async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=60.0) as client:
        conversation = (await client.post("/v1/conversations", json={})).json()
        conversation_id = conversation["id"]
        print(f"Conversation: {conversation_id}\n")

        for message in _MESSAGES:
            reply = (
                await client.post(
                    f"/v1/conversations/{conversation_id}/messages",
                    json={"content": message},
                )
            ).json()
            print(f"You:  {message}")
            print(f"Aria: {reply['reply']}\n")

        lead = (
            await client.post(
                f"/v1/conversations/{conversation_id}/lead",
                json={"name": "Dana", "email": "dana@acme.com", "company": "Acme"},
            )
        ).json()
        print(f"Captured lead: {lead['email']}")

        qualification = (await client.post(f"/v1/conversations/{conversation_id}/qualify")).json()
        print(f"Qualification: stage={qualification['stage']} score={qualification['score']}")

        booking = (
            await client.post(
                f"/v1/conversations/{conversation_id}/schedule-demo",
                json={"requested_time": "next Tuesday 2pm"},
            )
        ).json()
        print(f"Demo booked: {booking['requested_time']} ({booking['status']})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a demo sales conversation.")
    parser.add_argument("--api-key", required=True, help="API key (X-API-Key)")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    asyncio.run(main(args.api_key, args.base_url))
