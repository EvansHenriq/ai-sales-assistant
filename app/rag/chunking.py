"""Simple, deterministic text chunking for the knowledge base.

Splits on blank lines and greedily packs paragraphs into chunks up to a maximum
size. Deterministic so it can be unit-tested without external services.
"""


def chunk_text(text: str, *, max_chars: int = 800) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)
    return chunks
