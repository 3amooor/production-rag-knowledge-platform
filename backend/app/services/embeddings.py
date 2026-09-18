"""Deterministic local embeddings for development and integration tests.

The provider boundary is isolated here so a managed embedding service can replace it
without changing ingestion or retrieval.
"""

import hashlib
import math
import re

from app.core.config import get_settings

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def embed_text(text: str) -> list[float]:
    """Create a normalized hashing-vector embedding with the configured dimensionality."""

    dimensions = get_settings().embedding_dimensions
    vector = [0.0] * dimensions
    for token in TOKEN_PATTERN.findall(text.lower()):
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        vector[bucket] += 1.0 if digest[4] & 1 else -1.0
    magnitude = math.sqrt(sum(value * value for value in vector))
    return vector if magnitude == 0 else [value / magnitude for value in vector]
