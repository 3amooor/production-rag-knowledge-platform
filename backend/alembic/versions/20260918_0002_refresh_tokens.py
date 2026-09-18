"""Add revocable refresh-token records."""

from alembic import op

revision = "20260918_0002"
down_revision = "20260918_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TABLE refresh_tokens (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, token_hash VARCHAR(64) NOT NULL UNIQUE, expires_at TIMESTAMPTZ NOT NULL, revoked_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now());")
    op.execute("CREATE INDEX ix_refresh_tokens_user_expires ON refresh_tokens (user_id, expires_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS refresh_tokens")
