"""Tenant-scoped hybrid retrieval with reciprocal-rank fusion."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Chunk, Document
from app.services.embeddings import embed_text


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    filename: str
    score: float


def retrieve(
    session: Session, workspace_id: UUID, query: str, limit: int = 5
) -> list[RetrievedChunk]:
    """Return only chunks belonging to the authorized workspace.

    Dense and lexical candidates are independently gathered then fused with RRF. The
    workspace predicate is applied in both queries, never after retrieval.
    """

    candidate_count = max(limit * 4, 20)
    dense_rows = session.execute(
        select(Chunk, Document.filename)
        .join(Document, Document.id == Chunk.document_id)
        .where(Chunk.workspace_id == workspace_id)
        .order_by(Chunk.embedding.cosine_distance(embed_text(query)))
        .limit(candidate_count)
    ).all()
    lexical_rows = session.execute(
        select(Chunk, Document.filename)
        .join(Document, Document.id == Chunk.document_id)
        .where(
            Chunk.workspace_id == workspace_id,
            Chunk.search_vector.op("@@")(func.websearch_to_tsquery("english", query)),
        )
        .order_by(
            func.ts_rank_cd(
                Chunk.search_vector,
                func.websearch_to_tsquery("english", query),
            ).desc()
        )
        .limit(candidate_count)
    ).all()
    fused: dict[UUID, tuple[Chunk, str, float]] = {}
    for rows in (dense_rows, lexical_rows):
        for rank, (chunk, filename) in enumerate(rows, start=1):
            previous = fused.get(chunk.id)
            score = (previous[2] if previous else 0.0) + 1 / (60 + rank)
            fused[chunk.id] = (chunk, filename, score)
    ranked = sorted(fused.values(), key=lambda row: row[2], reverse=True)[:limit]
    return [
        RetrievedChunk(chunk=chunk, filename=filename, score=score)
        for chunk, filename, score in ranked
    ]
