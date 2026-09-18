from app.services.chunking import chunk_text
from app.services.embeddings import embed_text
from app.services.parsing import extract_text


def test_chunk_text_preserves_all_text_with_overlap() -> None:
    chunks = chunk_text("one two three four five six", chunk_size=13, overlap=4)

    assert len(chunks) > 1
    assert chunks[0].startswith("one")
    assert chunks[-1].endswith("six")


def test_embeddings_are_normalized_and_deterministic() -> None:
    first = embed_text("workspace scoped retrieval")

    assert first == embed_text("workspace scoped retrieval")
    assert len(first) == 1536
    assert round(sum(value * value for value in first), 6) == 1.0


def test_plain_text_parser_decodes_utf8() -> None:
    assert extract_text(b"knowledge base", "text/plain") == "knowledge base"
