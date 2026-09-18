"""Safe document text extraction for the first ingestion pipeline."""


def extract_text(content: bytes, content_type: str) -> str:
    """Extract text from the currently supported UTF-8 text formats."""

    if content_type in {"text/plain", "text/markdown"}:
        return content.decode("utf-8", errors="replace")
    raise ValueError(f"No parser is configured for {content_type}.")
