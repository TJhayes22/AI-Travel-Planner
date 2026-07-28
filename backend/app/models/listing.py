"""Listing and booking models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, SmallInteger, Text
from sqlalchemy.dialects.postgresql import CHAR, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination


class Listing(Base):
    """Accommodations and services at destinations (hotels, airbnbs, etc.)."""

    __tablename__ = "listings"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'published', 'archived')",
            name="chk_listings_status",
        ),
        CheckConstraint(
            "listing_type IN ('hotel', 'hostel', 'airbnb', 'resort', 'other')",
            name="chk_listings_type",
        ),
        Index("idx_listings_destination_id", "destination_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    destination_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    listing_type: Mapped[str] = mapped_column(Text, nullable=False)
    price_tier: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    price_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )
    rating: Mapped[Decimal | None] = mapped_column(Numeric(precision=2, scale=1), nullable=True)
    booking_url: Mapped[str] = mapped_column(Text, nullable=False)
    affiliate_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(
        CHAR(length=3), server_default="'USD'::bpchar", nullable=False, default="USD"
    )
    status: Mapped[str] = mapped_column(
        Text, server_default="'published'::text", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    destination: Mapped["Destination"] = relationship(
        "Destination", back_populates="listings", foreign_keys=[destination_id]
    )
    images: Mapped[list["ListingImage"]] = relationship(
        "ListingImage", back_populates="listing", cascade="all, delete-orphan"
    )


class ListingImage(Base):
    """Images associated with listings."""

    __tablename__ = "listing_images"

    __table_args__ = (
        Index("idx_listing_images_listing_id", "listing_id"),
        Index(
            "idx_listing_images_one_primary",
            "listing_id",
            unique=True,
            postgresql_where="is_primary",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    listing_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False
    )
    s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    alt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(server_default="false", nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, server_default="0", nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    listing: Mapped[Listing] = relationship(
        "Listing", back_populates="images", foreign_keys=[listing_id]
    )