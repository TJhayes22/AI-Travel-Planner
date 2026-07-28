"""Destination, raw scrape, and destination image models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, TSVECTOR, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.tag import DestinationTag, Tag


class RawScrape(Base):
    """Raw scraped data from external sources."""

    __tablename__ = "raw_scrapes"

    __table_args__ = (
        CheckConstraint(
            "status IN ('fetched', 'parsed', 'enriched', 'published', 'failed')",
            name="chk_raw_scrapes_status",
        ),
        Index("idx_raw_scrapes_status", "status"),
        Index("idx_raw_scrapes_content_hash", "content_hash"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    s3_raw_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB(astext_type=Text()), nullable=True)
    status: Mapped[str] = mapped_column(Text, server_default="'fetched'::text", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    destinations: Mapped[list["Destination"]] = relationship(
        "Destination", back_populates="raw_scrape"
    )


class Destination(Base):
    """Travel destination with metadata and embeddings."""

    __tablename__ = "destinations"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'enriched', 'published', 'archived')",
            name="chk_destinations_status",
        ),
        UniqueConstraint("slug"),
        Index("idx_destinations_status", "status"),
        Index(
            "idx_destinations_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("idx_destinations_search_vector", "search_vector", postgresql_using="gin"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    raw_scrape_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("raw_scrapes.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_tier: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    climate: Mapped[str | None] = mapped_column(Text, nullable=True)
    best_season: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, server_default="'draft'::text", nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(dim=1536), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, nullable=True
    )  # Trigger-maintained, do not set manually
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    raw_scrape: Mapped[RawScrape | None] = relationship(
        "RawScrape", back_populates="destinations", foreign_keys=[raw_scrape_id]
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="destination_tags",
        back_populates="destinations",
    )
    images: Mapped[list["DestinationImage"]] = relationship(
        "DestinationImage", back_populates="destination", cascade="all, delete-orphan"
    )
    listings: Mapped[list["Listing"]] = relationship(
        "Listing", back_populates="destination", cascade="all, delete-orphan"
    )


class DestinationImage(Base):
    """Images associated with destinations."""

    __tablename__ = "destination_images"

    __table_args__ = (
        Index("idx_destination_images_destination_id", "destination_id"),
        Index(
            "idx_destination_images_one_primary",
            "destination_id",
            unique=True,
            postgresql_where="is_primary",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    destination_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False
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
    destination: Mapped[Destination] = relationship(
        "Destination", back_populates="images", foreign_keys=[destination_id]
    )


# Import Tag after Destination to avoid circular imports
from app.models.tag import Tag  # noqa: E402