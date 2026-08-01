"""ORM mapping for public.business_memory.

Maps 1:1 onto supabase/migrations/20260801100007_business_memory_and_embeddings.sql
(the business_memory half — see memory_embedding.py for the other table it
defines).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MemorySource, MemoryType, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.conversation_history import ConversationHistory
    from app.models.memory_embedding import MemoryEmbedding
    from app.models.voice_log import VoiceLog


class BusinessMemory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "business_memory"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        CheckConstraint(
            "importance_score between 1 and 5", name="chk_business_memory_importance"
        ),
    )

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_voice_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("voice_logs.id", ondelete="SET NULL"),
    )
    memory_type: Mapped[MemoryType] = mapped_column(
        pg_enum(MemoryType, "memory_type_enum"),
        nullable=False,
        server_default=MemoryType.NOTE.value,
    )
    title: Mapped[str | None] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[MemorySource] = mapped_column(
        pg_enum(MemorySource, "memory_source_enum"),
        nullable=False,
        server_default=MemorySource.MANUAL.value,
    )
    importance_score: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="3"
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="memories"
    )
    source_voice_log: Mapped["VoiceLog | None"] = relationship(
        back_populates="sourced_memories"
    )
    embeddings: Mapped[list["MemoryEmbedding"]] = relationship(
        back_populates="business_memory"
    )
    related_conversation_turns: Mapped[list["ConversationHistory"]] = relationship(
        back_populates="related_memory"
    )


Index(
    "idx_business_memory_business_profile",
    BusinessMemory.business_profile_id,
    BusinessMemory.created_at.desc(),
)
Index("idx_business_memory_type", BusinessMemory.memory_type)
Index(
    "idx_business_memory_active",
    BusinessMemory.business_profile_id,
    postgresql_where=(BusinessMemory.is_archived.is_(False)),
)
Index("idx_business_memory_source_voice_log", BusinessMemory.source_voice_log_id)
