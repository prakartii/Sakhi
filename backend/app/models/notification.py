"""ORM mapping for public.notifications.

Maps 1:1 onto supabase/migrations/20260801100016_forecast_and_notifications.sql
(the notifications half — see forecast_history.py for the other table it
defines), plus the one cross-table index migration 17 adds against this
table.

related_entity_type / related_entity_id are deliberately NOT a relationship()
or ForeignKey — same as in the SQL migration, this is an intentionally
unenforced polymorphic pointer (it can reference a row in scheme_matches,
inventory, forecast_history, etc.), not a single fixed target table.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    NotificationChannel,
    NotificationPriority,
    NotificationType,
    pg_enum,
)
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.user import User


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notifications"
    __mapper_args__ = {"eager_defaults": True}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    business_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        pg_enum(NotificationType, "notification_type_enum"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    action_url: Mapped[str | None] = mapped_column(Text)
    related_entity_type: Mapped[str | None] = mapped_column(String(50))
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    channel: Mapped[NotificationChannel] = mapped_column(
        pg_enum(NotificationChannel, "notification_channel_enum"),
        nullable=False,
        server_default=NotificationChannel.IN_APP.value,
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        pg_enum(NotificationPriority, "notification_priority_enum"),
        nullable=False,
        server_default=NotificationPriority.NORMAL.value,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # -- relationships ----------------------------------------------------
    user: Mapped["User"] = relationship(back_populates="notifications")
    business_profile: Mapped["BusinessProfile | None"] = relationship(
        back_populates="notifications"
    )


Index(
    "idx_notifications_user_unread",
    Notification.user_id,
    Notification.created_at.desc(),
    postgresql_where=(Notification.is_read.is_(False)),
)
Index("idx_notifications_business_profile", Notification.business_profile_id)
Index("idx_notifications_type", Notification.notification_type)
Index(
    "idx_notifications_related_entity",
    Notification.related_entity_type,
    Notification.related_entity_id,
)
# From supabase/migrations/20260801100017_performance_indexes.sql.
Index(
    "idx_notifications_user_type_unread",
    Notification.user_id,
    Notification.notification_type,
    postgresql_where=(Notification.is_read.is_(False)),
)
