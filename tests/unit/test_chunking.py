from app.rag.chunking import chunk_text


def test_chunk_text_returns_empty_for_blank() -> None:
    assert chunk_text("   \n\n  ") == []


def test_chunk_text_packs_small_paragraphs_into_one() -> None:
    assert chunk_text("a\n\nb\n\nc", max_chars=100) == ["a\n\nb\n\nc"]


def test_chunk_text_splits_when_exceeding_max() -> None:
    text = "paragraph one\n\nparagraph two\n\nparagraph three"
    chunks = chunk_text(text, max_chars=15)
    assert len(chunks) == 3
    assert all(chunk.strip() for chunk in chunks)
    joined = "\n\n".join(chunks)
    assert "paragraph one" in joined
    assert "paragraph three" in joined
