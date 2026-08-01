"""ORM mapping for public.conversation_history.

Maps 1:1 onto supabase/migrations/20260801100008_conversation_history.sql.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ConversationMessageType, ConversationRole, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_memory import BusinessMemory
    from app.models.business_profile import BusinessProfile
    from app.models.user import User
    from app.models.voice_log import VoiceLog


class ConversationHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversation_history"
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
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    role: Mapped[ConversationRole] = mapped_column(
        pg_enum(ConversationRole, "conversation_role_enum"), nullable=False
    )
    message_type: Mapped[ConversationMessageType] = mapped_column(
        pg_enum(ConversationMessageType, "conversation_message_type_enum"),
        nullable=False,
        server_default=ConversationMessageType.TEXT.value,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    related_voice_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("voice_logs.id", ondelete="SET NULL"),
    )
    related_memory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_memory.id", ondelete="SET NULL"),
    )

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="conversation_turns"
    )
    user: Mapped["User"] = relationship(back_populates="conversation_turns")
    related_voice_log: Mapped["VoiceLog | None"] = relationship(
        back_populates="related_conversation_turns"
    )
    related_memory: Mapped["BusinessMemory | None"] = relationship(
        back_populates="related_conversation_turns"
    )


Index(
    "idx_conversation_history_session",
    ConversationHistory.session_id,
    ConversationHistory.created_at,
)
Index(
    "idx_conversation_history_business_profile",
    ConversationHistory.business_profile_id,
    ConversationHistory.created_at.desc(),
)
Index("idx_conversation_history_related_memory", ConversationHistory.related_memory_id)
