"""Itinerary and travel plan models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination
    from app.models.user import User


class Itinerary(Base):
    """AI-generated travel itinerary for a destination."""

    __tablename__ = "itineraries"

    __table_args__ = (
        UniqueConstraint("cache_key"),
        Index("idx_itineraries_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    destination_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False
    )
    cache_key: Mapped[str] = mapped_column(Text, nullable=False)
    input_params: Mapped[dict] = mapped_column(
        JSONB(astext_type=Text()), server_default="'{}'::jsonb", nullable=False
    )
    generated_content: Mapped[dict] = mapped_column(
        JSONB(astext_type=Text()), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="itineraries", foreign_keys=[user_id])
    destination: Mapped["Destination"] = relationship(
        "Destination", foreign_keys=[destination_id]
    )