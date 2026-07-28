"""Tag models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination


class Tag(Base):
    """Tags for categorizing destinations."""

    __tablename__ = "tags"

    __table_args__ = (
        CheckConstraint(
            "category IN ('vibe', 'activity', 'climate', 'cost', 'other')",
            name="chk_tags_category",
        ),
        UniqueConstraint("name"),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    destinations: Mapped[list["Destination"]] = relationship(
        "Destination",
        secondary="destination_tags",
        back_populates="tags",
    )


class DestinationTag(Base):
    """Association table between destinations and tags (many-to-many)."""

    __tablename__ = "destination_tags"

    __table_args__ = (Index("idx_destination_tags_tag_id", "tag_id"),)

    destination_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("destinations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )