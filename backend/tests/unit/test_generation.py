from dataclasses import dataclass
from uuid import uuid4

from app.services.generation import build_extractive_answer
from app.services.retrieval import RetrievedChunk


@dataclass
class FakeChunk:
    content: str
    id: object = None
    document_id: object = None


def result(content: str) -> RetrievedChunk:
    chunk = FakeChunk(content=content, id=uuid4(), document_id=uuid4())
    return RetrievedChunk(chunk=chunk, filename="source.md", score=1.0)  # type: ignore[arg-type]


def test_extractive_answer_prefers_query_terms_and_removes_duplicates() -> None:
    duplicate = "The platform is currently in Phase 22 and is ready for local release."
    answer = build_extractive_answer(
        "What phase is the platform currently in?",
        [result(f"Background information. {duplicate}"), result(duplicate)],
    )

    assert answer.startswith(duplicate)
    assert answer.count(duplicate) == 1


def test_extractive_answer_handles_no_results() -> None:
    assert "could not find" in build_extractive_answer("missing", [])
