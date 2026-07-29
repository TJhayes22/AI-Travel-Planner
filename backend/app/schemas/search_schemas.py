"""Response schemas for the search endpoint."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    id: UUID
    name: str
    slug: str
    country: str | None
    region: str | None
    description: str | None
    cost_tier: int | None
    tags: list[str]
    similarity_score: float  # 0.0 (no similarity) to 1.0 (identical)

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]