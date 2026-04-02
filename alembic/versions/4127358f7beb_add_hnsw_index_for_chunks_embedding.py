"""为 chunks embedding 添加 HNSW 索引

Revision ID: 4127358f7beb
Revises: 89cb75f20cdc
Create Date: 2026-03-16 15:06:43.012468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic 使用的版本标识符
revision: str = '4127358f7beb'
down_revision: Union[str, Sequence[str], None] = '89cb75f20cdc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库架构"""
    op.execute("""
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
ON chunks
USING hnsw (embedding vector_cosine_ops);
""")


def downgrade() -> None:
    """降级数据库架构"""
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding_hnsw;")
