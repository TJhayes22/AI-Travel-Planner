"""User and preference models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination
    from app.models.itinerary import Itinerary
    from app.models.listing import Listing


class User(Base):
    """User account."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    auth_provider_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    preference: Mapped["UserPreference | None"] = relationship(
        "UserPreference", back_populates="user", foreign_keys="UserPreference.user_id", uselist=False, cascade="all, delete-orphan"
    )
    interactions: Mapped[list["UserInteraction"]] = relationship(
        "UserInteraction", back_populates="user", cascade="all, delete-orphan"
    )
    itineraries: Mapped[list["Itinerary"]] = relationship(
        "Itinerary", back_populates="user", cascade="all, delete-orphan"
    )


class UserPreference(Base):
    """User AI preferences and embedding."""

    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    raw_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_tags: Mapped[dict] = mapped_column(
        JSONB(astext_type=Text()), server_default="'{}'::jsonb", nullable=False
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(dim=1536), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="preference", foreign_keys=[user_id])


class UserInteraction(Base):
    """User actions on destinations and listings."""

    __tablename__ = "user_interactions"

    __table_args__ = (
        CheckConstraint(
            "interaction_type IN ('viewed', 'saved', 'searched', 'booking_click', 'rated')",
            name="chk_user_interactions_type",
        ),
        CheckConstraint(
            "user_id IS NOT NULL OR session_id IS NOT NULL",
            name="chk_user_interactions_identity",
        ),
        Index("idx_user_interactions_user_id", "user_id"),
        Index("idx_user_interactions_destination_id", "destination_id"),
        Index("idx_user_interactions_session_id", "session_id"),
        Index("idx_user_interactions_type", "interaction_type"),
        Index("idx_user_interactions_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, autoincrement=True, primary_key=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    destination_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=True,
    )
    listing_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True
    )
    interaction_type: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    interaction_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB(astext_type=Text()), server_default="'{}'::jsonb", nullable=False
    )
    session_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    user: Mapped[User | None] = relationship("User", back_populates="interactions", foreign_keys=[user_id])
    destination: Mapped["Destination | None"] = relationship(
        "Destination", foreign_keys=[destination_id], viewonly=True
    )
    listing: Mapped["Listing | None"] = relationship("Listing", foreign_keys=[listing_id], viewonly=True)