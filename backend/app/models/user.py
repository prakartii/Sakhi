"""ORM mapping for public.users.

Maps 1:1 onto supabase/migrations/20260801100004_users_and_preferences.sql
(the users half — see user_preferences.py for the other table it defines).

`id` deliberately does NOT use UUIDPrimaryKeyMixin: unlike every other table,
users.id has no `default gen_random_uuid()` of its own — it IS a foreign key
to Supabase's built-in auth.users(id), whose value auth issues at signup.
Modeling that FK is not implementing authentication; it's the same
schema-accurate mapping this task asks for applied to a column that happens
to point at a schema Supabase, not this app, owns and migrates.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserStatus, pg_enum
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.conversation_history import ConversationHistory
    from app.models.language import Language
    from app.models.mentor_profile import MentorProfile
    from app.models.notification import Notification
    from app.models.user_preferences import UserPreferences
    from app.models.voice_log import VoiceLog

# NOT an ORM-mapped entity: auth.users is owned and migrated by Supabase's
# auth schema, not this app. SQLAlchemy still needs a Table with the
# referenced column present in the same MetaData to resolve the FK below —
# this is the minimum required for that, with no mapped class, so nothing
# can query or relationship() through it. Still not authentication.
Table(
    "users",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    schema="auth",
)


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    full_name: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    preferred_language_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("languages.id", ondelete="SET NULL"),
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    status: Mapped[UserStatus] = mapped_column(
        pg_enum(UserStatus, "user_status_enum"),
        nullable=False,
        server_default=UserStatus.ACTIVE.value,
    )

    # -- relationships ----------------------------------------------------
    preferred_language: Mapped["Language | None"] = relationship(back_populates="users")
    preferences: Mapped["UserPreferences | None"] = relationship(
        back_populates="user", uselist=False
    )
    business_profiles: Mapped[list["BusinessProfile"]] = relationship(
        back_populates="user"
    )
    voice_logs: Mapped[list["VoiceLog"]] = relationship(back_populates="user")
    conversation_turns: Mapped[list["ConversationHistory"]] = relationship(
        back_populates="user"
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
    mentor_profiles: Mapped[list["MentorProfile"]] = relationship(back_populates="user")


Index("idx_users_status", User.status)
Index("idx_users_preferred_language", User.preferred_language_id)
