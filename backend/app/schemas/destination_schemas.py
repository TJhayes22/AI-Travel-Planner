"""Response schemas for the destination detail endpoint."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ListingSummary(BaseModel):
    id: UUID
    name: str
    listing_type: str
    price_tier: int | None
    price_amount: Decimal | None
    currency: str
    rating: Decimal | None
    booking_url: str

    model_config = {"from_attributes": True}


class DestinationSummary(BaseModel):
    """Lighter-weight shape for list views (e.g. featured destinations on the
    landing page) -- no listings, matches SearchResultItem's shape minus the
    similarity_score, which only makes sense in a search context."""

    id: UUID
    name: str
    slug: str
    country: str | None
    region: str | None
    description: str | None
    cost_tier: int | None
    latitude: float | None
    longitude: float | None
    tags: list[str]

    model_config = {"from_attributes": True}


class DestinationDetail(BaseModel):
    id: UUID
    name: str
    slug: str
    country: str | None
    region: str | None
    description: str | None
    cost_tier: int | None
    climate: str | None
    best_season: str | None
    latitude: float | None
    longitude: float | None
    tags: list[str]
    listings: list[ListingSummary]

    model_config = {"from_attributes": True}