"""Create the initial multi-tenant RAG platform schema.

Revision ID: 20260918_0001
Revises:
Create Date: 2026-09-18
"""

from alembic import op

revision = "20260918_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create extensions, tenant-scoped entities, retrieval indexes, and telemetry tables."""

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(
        """
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(320) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE workspaces (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            name VARCHAR(160) NOT NULL,
            slug VARCHAR(180) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE workspace_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(16) NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_workspace_members_workspace_user UNIQUE (workspace_id, user_id)
        );
        CREATE TABLE documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            uploaded_by_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            filename VARCHAR(512) NOT NULL,
            content_type VARCHAR(255) NOT NULL,
            size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
            status VARCHAR(16) NOT NULL DEFAULT 'UPLOADED'
                CHECK (status IN ('UPLOADED', 'PROCESSING', 'READY', 'FAILED')),
            failure_reason TEXT,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE document_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            version_number INTEGER NOT NULL CHECK (version_number > 0),
            content_hash VARCHAR(64) NOT NULL,
            object_key VARCHAR(1024) NOT NULL UNIQUE,
            parser_version VARCHAR(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_document_version_number UNIQUE (document_id, version_number),
            CONSTRAINT uq_document_content_hash UNIQUE (document_id, content_hash)
        );
        CREATE TABLE chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            embedding vector(1536) NOT NULL,
            search_vector TSVECTOR NOT NULL,
            page_number INTEGER CHECK (page_number IS NULL OR page_number > 0),
            chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
            token_count INTEGER NOT NULL CHECK (token_count >= 0),
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_chunk_version_index UNIQUE (document_version_id, chunk_index)
        );
        CREATE TABLE conversations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            created_by_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            title VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role VARCHAR(16) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'COMPLETE'
                CHECK (status IN ('PENDING', 'COMPLETE', 'FAILED')),
            citations JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE retrieval_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
            strategy VARCHAR(32) NOT NULL,
            query_hash VARCHAR(64) NOT NULL,
            retrieved_chunks JSONB NOT NULL,
            latency_ms INTEGER NOT NULL CHECK (latency_ms >= 0),
            configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE generation_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            message_id UUID NOT NULL UNIQUE REFERENCES messages(id) ON DELETE CASCADE,
            model VARCHAR(128) NOT NULL,
            input_tokens INTEGER CHECK (input_tokens IS NULL OR input_tokens >= 0),
            output_tokens INTEGER CHECK (output_tokens IS NULL OR output_tokens >= 0),
            latency_ms INTEGER NOT NULL CHECK (latency_ms >= 0),
            estimated_cost_usd DOUBLE PRECISION CHECK (estimated_cost_usd IS NULL OR estimated_cost_usd >= 0),
            error_code VARCHAR(128),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE evaluation_datasets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            version VARCHAR(64) NOT NULL,
            description TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_evaluation_dataset UNIQUE (workspace_id, name, version)
        );
        CREATE TABLE evaluation_questions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            dataset_id UUID NOT NULL REFERENCES evaluation_datasets(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            expected_answer TEXT,
            relevant_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            tags JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE evaluation_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            dataset_id UUID NOT NULL REFERENCES evaluation_datasets(id) ON DELETE RESTRICT,
            status VARCHAR(16) NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETE', 'FAILED')),
            configuration JSONB NOT NULL,
            metrics JSONB,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE processing_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            document_version_id UUID NOT NULL UNIQUE REFERENCES document_versions(id) ON DELETE CASCADE,
            status VARCHAR(16) NOT NULL DEFAULT 'QUEUED'
                CHECK (status IN ('QUEUED', 'PROCESSING', 'COMPLETE', 'FAILED')),
            attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
            error_message TEXT,
            locked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX ix_workspace_members_user_workspace ON workspace_members (user_id, workspace_id);
        CREATE INDEX ix_documents_workspace_created ON documents (workspace_id, created_at DESC);
        CREATE INDEX ix_document_versions_document ON document_versions (document_id, version_number DESC);
        CREATE INDEX ix_chunks_workspace_document ON chunks (workspace_id, document_id);
        CREATE INDEX ix_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        CREATE INDEX ix_chunks_search_vector ON chunks USING gin (search_vector);
        CREATE INDEX ix_conversations_workspace_created ON conversations (workspace_id, created_at DESC);
        CREATE INDEX ix_messages_conversation_created ON messages (conversation_id, created_at);
        CREATE INDEX ix_retrieval_logs_workspace_created ON retrieval_logs (workspace_id, created_at DESC);
        CREATE INDEX ix_evaluation_runs_dataset_created ON evaluation_runs (dataset_id, created_at DESC);
        CREATE INDEX ix_processing_jobs_status_created ON processing_jobs (status, created_at);
        """
    )


def downgrade() -> None:
    """Remove application-owned schema objects in dependency order."""

    op.execute(
        """
        DROP TABLE IF EXISTS processing_jobs;
        DROP TABLE IF EXISTS evaluation_runs;
        DROP TABLE IF EXISTS evaluation_questions;
        DROP TABLE IF EXISTS evaluation_datasets;
        DROP TABLE IF EXISTS generation_logs;
        DROP TABLE IF EXISTS retrieval_logs;
        DROP TABLE IF EXISTS messages;
        DROP TABLE IF EXISTS conversations;
        DROP TABLE IF EXISTS chunks;
        DROP TABLE IF EXISTS document_versions;
        DROP TABLE IF EXISTS documents;
        DROP TABLE IF EXISTS workspace_members;
        DROP TABLE IF EXISTS workspaces;
        DROP TABLE IF EXISTS users;
        """
    )
