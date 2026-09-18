import app.models  # noqa: F401
from app.db.base import Base


def test_initial_schema_exposes_required_tables() -> None:
    expected_tables = {
        "users",
        "workspaces",
        "workspace_members",
        "documents",
        "document_versions",
        "chunks",
        "conversations",
        "messages",
        "retrieval_logs",
        "generation_logs",
        "evaluation_datasets",
        "evaluation_questions",
        "evaluation_runs",
        "processing_jobs",
    }

    assert expected_tables <= set(Base.metadata.tables)


def test_chunks_define_tenant_and_retrieval_indexes() -> None:
    chunks = Base.metadata.tables["chunks"]
    index_names = {index.name for index in chunks.indexes}

    assert {
        "ix_chunks_workspace_document",
        "ix_chunks_embedding_hnsw",
        "ix_chunks_search_vector",
    } <= index_names
