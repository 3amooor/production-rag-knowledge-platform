"""Workspace-scoped conversation and grounded-answer endpoints."""

from hashlib import sha256
from time import perf_counter
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.security import get_current_user, require_workspace_member
from app.db.session import get_db_session
from app.models import Conversation, GenerationLog, Message, RetrievalLog, User
from app.schemas.rag import (
    AnswerResponse,
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.generation import build_extractive_answer
from app.services.retrieval import retrieve

router = APIRouter(prefix="/workspaces/{workspace_id}/conversations", tags=["conversations"])


def _citations(results: list) -> list[dict]:
    return [
        {
            "chunk_id": str(result.chunk.id),
            "document_id": str(result.chunk.document_id),
            "filename": result.filename,
            "excerpt": result.chunk.content[:500],
            "score": round(result.score, 6),
        }
        for result in results
    ]


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    workspace_id: UUID,
    payload: ConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[object, Depends(require_workspace_member)],
    session: Annotated[Session, Depends(get_db_session)],
) -> Conversation:
    conversation = Conversation(
        workspace_id=workspace_id, created_by_id=current_user.id, title=payload.title
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(
    workspace_id: UUID,
    conversation_id: UUID,
    _: Annotated[object, Depends(require_workspace_member)],
    session: Annotated[Session, Depends(get_db_session)],
) -> list[Message]:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None or conversation.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return list(
        session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=AnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
def ask_question(
    workspace_id: UUID,
    conversation_id: UUID,
    payload: MessageCreate,
    _: Annotated[object, Depends(require_workspace_member)],
    session: Annotated[Session, Depends(get_db_session)],
) -> AnswerResponse:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None or conversation.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    user_message = Message(conversation_id=conversation_id, role="user", content=payload.content)
    session.add(user_message)
    session.flush()
    started_at = perf_counter()
    results = retrieve(session, workspace_id, payload.content)
    citations = _citations(results)
    answer = build_extractive_answer(payload.content, results)
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        citations=citations,
    )
    session.add(assistant_message)
    session.flush()
    latency_ms = int((perf_counter() - started_at) * 1_000)
    session.add(
        RetrievalLog(
            workspace_id=workspace_id,
            message_id=assistant_message.id,
            strategy="hybrid_rrf",
            query_hash=sha256(payload.content.encode()).hexdigest(),
            retrieved_chunks=citations,
            latency_ms=latency_ms,
            configuration={"limit": 5, "rrf_k": 60},
        )
    )
    session.add(
        GenerationLog(
            message_id=assistant_message.id,
            model="extractive-v1",
            latency_ms=latency_ms,
        )
    )
    session.commit()
    session.refresh(user_message)
    session.refresh(assistant_message)
    return AnswerResponse(user_message=user_message, assistant_message=assistant_message)
