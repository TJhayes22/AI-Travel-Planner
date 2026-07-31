"""Destination detail endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.destination import Destination
from app.schemas.destination_schemas import DestinationDetail, ListingSummary

router = APIRouter()


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