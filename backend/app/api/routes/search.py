"""Destination search endpoint: free text -> embedding -> pgvector similarity search."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.destination import Destination
from app.schemas.search_schemas import SearchResponse, SearchResultItem
from app.services.embeddings import get_query_embedding

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_destinations(
    q: str = Query(..., min_length=1, max_length=500, description="Free-text search query"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    query_embedding = get_query_embedding(q)

    # cosine_distance: 0.0 = identical, 2.0 = opposite. Convert to a more
    # intuitive similarity_score (1.0 = identical, 0.0 = no similarity) for
    # the response, while ordering by distance ascending under the hood.
    distance = Destination.embedding.cosine_distance(query_embedding)

    stmt = (
        select(Destination, distance.label("distance"))
        .options(selectinload(Destination.tags))
        .where(Destination.status == "published")
        .order_by(distance)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    results = [
        SearchResultItem(
            id=destination.id,
            name=destination.name,
            slug=destination.slug,
            country=destination.country,
            region=destination.region,
            description=destination.description,
            cost_tier=destination.cost_tier,
            tags=[tag.name for tag in destination.tags],
            similarity_score=max(0.0, 1.0 - (dist / 2.0)),
        )
        for destination, dist in rows
    ]

    return SearchResponse(query=q, results=results)