"""Small, inspectable extractive answer generation utilities."""

import re
from collections.abc import Iterable

from app.services.retrieval import RetrievedChunk

WORD_PATTERN = re.compile(r"[a-z0-9]+")
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "in",
    "is",
    "of",
    "the",
    "to",
    "what",
}


def _terms(text: str) -> set[str]:
    return {term for term in WORD_PATTERN.findall(text.lower()) if term not in STOP_WORDS}


def build_extractive_answer(
    question: str,
    results: Iterable[RetrievedChunk],
    *,
    max_sentences: int = 3,
) -> str:
    """Select concise, non-duplicated sentences with the best query overlap."""

    query_terms = _terms(question)
    candidates: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    order = 0
    for result in results:
        for raw_sentence in SENTENCE_PATTERN.split(result.chunk.content):
            sentence = " ".join(raw_sentence.split()).strip(" -")
            normalized = sentence.casefold()
            if len(sentence) < 20 or normalized in seen:
                continue
            seen.add(normalized)
            score = len(query_terms & _terms(sentence))
            candidates.append((score, -order, sentence))
            order += 1

    if not candidates:
        return "I could not find relevant information in this workspace yet."

    ranked = sorted(candidates, reverse=True)
    selected = [sentence for _, _, sentence in ranked[:max_sentences]]
    return " ".join(selected)
