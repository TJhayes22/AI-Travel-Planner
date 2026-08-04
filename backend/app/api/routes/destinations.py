"""Destination detail and list endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.destination import Destination
from app.schemas.destination_schemas import DestinationDetail, DestinationSummary, ListingSummary

router = APIRouter()


@router.get("/destinations", response_model=list[DestinationSummary])
async def list_destinations(
    limit: int = Query(6, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[DestinationSummary]:
    """Returns a random sample of published destinations -- used for the
    landing page's featured teaser strip. Random ordering is a deliberate
    choice for now, since there's no meaningful ranking signal (popularity,
    recency) yet with a small hand-picked catalog."""
    stmt = (
        select(Destination)
        .options(selectinload(Destination.tags))
        .where(Destination.status == "published")
        .order_by(func.random())
        .limit(limit)
    )

    result = await db.execute(stmt)
    destinations = result.scalars().all()

    return [
        DestinationSummary(
            id=d.id,
            name=d.name,
            slug=d.slug,
            country=d.country,
            region=d.region,
            description=d.description,
            cost_tier=d.cost_tier,
            latitude=d.latitude,
            longitude=d.longitude,
            tags=[tag.name for tag in d.tags],
        )
        for d in destinations
    ]


@router.get("/destinations/{slug}", response_model=DestinationDetail)
async def get_destination(slug: str, db: AsyncSession = Depends(get_db)) -> DestinationDetail:
    stmt = (
        select(Destination)
        .options(
            selectinload(Destination.tags),
            selectinload(Destination.listings),
        )
        .where(Destination.slug == slug, Destination.status == "published")
    )

    result = await db.execute(stmt)
    destination = result.scalar_one_or_none()

    if destination is None:
        raise HTTPException(status_code=404, detail=f"Destination '{slug}' not found")

    return DestinationDetail(
        id=destination.id,
        name=destination.name,
        slug=destination.slug,
        country=destination.country,
        region=destination.region,
        description=destination.description,
        cost_tier=destination.cost_tier,
        climate=destination.climate,
        best_season=destination.best_season,
        latitude=destination.latitude,
        longitude=destination.longitude,
        tags=[tag.name for tag in destination.tags],
        listings=[ListingSummary.model_validate(listing) for listing in destination.listings],
    )