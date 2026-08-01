"""ORM mapping for public.memory_embeddings.

Maps 1:1 onto supabase/migrations/20260801100007_business_memory_and_embeddings.sql
(the memory_embeddings half). The `embedding vector(...)` column is commented
out in that migration pending pgvector being enabled, so — to stay an exact
match of what's actually in the database today — it's omitted here too. Add
it (as `sqlalchemy.dialects.postgresql.Vector` or the pgvector-sqlalchemy
`Vector` type) once a future migration actually creates the column.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_memory import BusinessMemory


class MemoryEmbedding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "memory_embeddings"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        UniqueConstraint(
            "business_memory_id", "chunk_index", name="uq_memory_embeddings_chunk"
        ),
    )

    business_memory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_memory.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(String(100))

    # -- relationships ----------------------------------------------------
    business_memory: Mapped["BusinessMemory"] = relationship(
        back_populates="embeddings"
    )


Index("idx_memory_embeddings_business_memory", MemoryEmbedding.business_memory_id)
