"""ORM mapping for public.voice_logs.

Maps 1:1 onto supabase/migrations/20260801100006_voice_logs.sql.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import VoiceLogStatus, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_memory import BusinessMemory
    from app.models.business_profile import BusinessProfile
    from app.models.conversation_history import ConversationHistory
    from app.models.language import Language
    from app.models.user import User


class VoiceLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "voice_logs"
    __mapper_args__ = {"eager_defaults": True}

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    language_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("languages.id", ondelete="SET NULL"),
    )
    audio_storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    transcript: Mapped[str | None] = mapped_column(Text)
    transcript_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    sentiment: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[VoiceLogStatus] = mapped_column(
        pg_enum(VoiceLogStatus, "voice_log_status_enum"),
        nullable=False,
        server_default=VoiceLogStatus.PENDING.value,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="voice_logs"
    )
    user: Mapped["User"] = relationship(back_populates="voice_logs")
    language: Mapped["Language | None"] = relationship(back_populates="voice_logs")
    sourced_memories: Mapped[list["BusinessMemory"]] = relationship(
        back_populates="source_voice_log"
    )
    related_conversation_turns: Mapped[list["ConversationHistory"]] = relationship(
        back_populates="related_voice_log"
    )


Index(
    "idx_voice_logs_business_profile",
    VoiceLog.business_profile_id,
    VoiceLog.recorded_at.desc(),
)
Index("idx_voice_logs_user", VoiceLog.user_id)
Index(
    "idx_voice_logs_status",
    VoiceLog.status,
    postgresql_where=VoiceLog.status.in_(
        [VoiceLogStatus.PENDING, VoiceLogStatus.PROCESSING]
    ),
)
