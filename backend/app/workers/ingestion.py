"""Idempotent background document processing."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func

from app.db.session import SessionLocal
from app.models import Chunk, Document, DocumentVersion, ProcessingJob
from app.services.chunking import chunk_text
from app.services.embeddings import embed_text
from app.services.parsing import extract_text
from app.services.storage import get_document
from app.workers.celery_app import celery_app


@celery_app.task(
    name="app.workers.ingestion.process_document",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def process_document(job_id: str) -> None:
    """Extract, chunk, and index one version; safe to retry after worker failure."""

    session = SessionLocal()
    try:
        job = session.get(ProcessingJob, UUID(job_id))
        if job is None or job.status == "COMPLETE":
            return
        job.status = "PROCESSING"
        job.attempts += 1
        job.locked_at = datetime.now(UTC)
        document = session.get(Document, job.document_id)
        version = session.get(DocumentVersion, job.document_version_id)
        if document is None or version is None:
            raise RuntimeError("Processing job references a missing document version.")
        document.status = "PROCESSING"
        session.commit()

        raw_text = extract_text(get_document(version.object_key), document.content_type)
        chunks = chunk_text(raw_text)
        if not chunks:
            raise ValueError("The document contains no indexable text.")

        session.execute(delete(Chunk).where(Chunk.document_version_id == version.id))
        for index, content in enumerate(chunks):
            session.add(
                Chunk(
                    workspace_id=document.workspace_id,
                    document_id=document.id,
                    document_version_id=version.id,
                    content=content,
                    embedding=embed_text(content),
                    search_vector=func.to_tsvector("english", content),
                    chunk_index=index,
                    token_count=len(content.split()),
                )
            )
        job.status = "COMPLETE"
        document.status = "READY"
        document.failure_reason = None
        session.commit()
    except Exception as exc:
        session.rollback()
        job = session.get(ProcessingJob, UUID(job_id))
        if job is not None:
            job.status = "FAILED"
            job.error_message = str(exc)[:2_000]
            document = session.get(Document, job.document_id)
            if document is not None:
                document.status = "FAILED"
                document.failure_reason = job.error_message
            session.commit()
        raise
    finally:
        session.close()
