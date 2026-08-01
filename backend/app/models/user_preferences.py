"""ORM mapping for public.user_preferences.

Maps 1:1 onto supabase/migrations/20260801100004_users_and_preferences.sql
(the user_preferences half). unique=True on user_id both enforces the 1:1
relationship at the DB level and backs the User.preferences relationship
(uselist=False on the User side — see user.py).
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserPreferences(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_preferences"
    __mapper_args__ = {"eager_defaults": True}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="INR"
    )
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Asia/Kolkata"
    )
    theme: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="system"
    )
    notify_email: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    notify_sms: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    notify_push: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    notify_whatsapp: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    digest_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="daily"
    )

    # -- relationships ----------------------------------------------------
    user: Mapped["User"] = relationship(back_populates="preferences")
