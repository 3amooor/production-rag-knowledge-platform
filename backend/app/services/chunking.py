"""Text normalization and bounded overlapping chunking for ingestion."""

import re

WHITESPACE = re.compile(r"\s+")


def chunk_text(text: str, chunk_size: int = 1_000, overlap: int = 150) -> list[str]:
    """Split normalized text on word boundaries with deterministic overlap."""

    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    normalized = WHITESPACE.sub(" ", text).strip()
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunks.append(normalized[start:end].strip())
        if end == len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks
