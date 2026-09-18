from hashlib import sha256
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.security import get_current_user, require_workspace_member
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models import Document, DocumentVersion, ProcessingJob, User
from app.schemas.documents import DocumentResponse
from app.services.storage import StorageError, create_document_key, put_document
from app.workers.ingestion import process_document

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["documents"])
ALLOWED_TYPES = {"text/plain", "text/markdown"}


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    workspace_id: UUID,
    _: Annotated[object, Depends(require_workspace_member)],
    session: Annotated[Session, Depends(get_db_session)],
) -> list[Document]:
    return list(
        session.scalars(
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .order_by(Document.created_at.desc())
        )
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_status(
    workspace_id: UUID,
    document_id: UUID,
    _: Annotated[object, Depends(require_workspace_member)],
    session: Annotated[Session, Depends(get_db_session)],
) -> Document:
    document = session.get(Document, document_id)
    if document is None or document.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    workspace_id: UUID,
    upload: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[object, Depends(require_workspace_member)],
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str]:
    if upload.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported document type.")
    body = await upload.read(get_settings().max_upload_bytes + 1)
    if not body:
        raise HTTPException(status_code=422, detail="Document is empty.")
    if len(body) > get_settings().max_upload_bytes:
        raise HTTPException(status_code=413, detail="Document exceeds upload size limit.")
    filename = (upload.filename or "document").replace("\\", "/").split("/")[-1]
    document = Document(
        workspace_id=workspace_id,
        uploaded_by_id=current_user.id,
        filename=filename,
        content_type=upload.content_type,
        size_bytes=len(body),
    )
    session.add(document)
    session.flush()
    key = create_document_key(workspace_id, document.id)
    try:
        put_document(key, body, upload.content_type)
    except StorageError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="Document storage is unavailable.") from exc
    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        content_hash=sha256(body).hexdigest(),
        object_key=key,
        parser_version="text-v1",
    )
    session.add(version)
    session.flush()
    job = ProcessingJob(
        workspace_id=workspace_id,
        document_id=document.id,
        document_version_id=version.id,
    )
    session.add(job)
    session.commit()
    process_document.delay(str(job.id))
    return {"document_id": str(document.id), "status": "UPLOADED"}
