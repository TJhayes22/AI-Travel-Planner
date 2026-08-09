"""Publish stage: upsert enriched data into destinations."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.destination import (
    Destination,
    RawScrape,
)
from app.models.tag import (
    DestinationTag,
    Tag,
)
from ingestion.utils import (
    get_destination_summary,
    normalize_parsed_data,
    slug_to_display_name,
)


def slugify(value: str) -> str:
    """Convert text into a URL/database-friendly slug."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


async def publish_raw_scrape(
    raw_scrape_id: Any,
) -> Destination:
    """Publish one enriched RawScrape."""

    async with AsyncSessionLocal() as session:
        raw = await session.get(
            RawScrape,
            raw_scrape_id,
        )

        if raw is None:
            raise ValueError(
                f"raw_scrape not found: {raw_scrape_id}"
            )

        parsed = normalize_parsed_data(
            raw.parsed_data
        )

        display_name = parsed.get("title", "").strip()

        if not display_name:
            display_name = slug_to_display_name(
                raw.source_url.rstrip("/").split("/")[-1]
            )

        country = parsed.get("country", "").strip()

        if country:
            slug = f"{slugify(display_name)}-{slugify(country)}"
        else:
            slug = slugify(display_name)

        summary_text = get_destination_summary(parsed)

        result = await session.execute(
            select(Destination).where(
                Destination.slug == slug
            )
        )

        dest = result.scalar_one_or_none()

        if dest is None:
            dest = Destination(
                slug=slug
            )
            session.add(dest)

        # Core destination fields.
        dest.name = display_name
        dest.description = summary_text

        # Geography.
        dest.country = parsed.get("country")
        dest.region = parsed.get("region")
        dest.latitude = parsed.get(
            "latitude"
        )
        dest.longitude = parsed.get(
            "longitude"
        )

        # Enrichment fields.
        dest.cost_tier = parsed.get(
            "cost_tier"
        )
        dest.climate = parsed.get(
            "climate"
        )
        dest.best_season = parsed.get(
            "best_season"
        )

        # Embedding.
        dest.embedding = parsed.get(
            "embedding"
        )

        dest.embedding_model = parsed.get(
            "embedding_model"
        )

        dest.embedding_updated_at = (
            datetime.now(timezone.utc)
        )

        dest.status = "published"

        await session.flush()

        # Source URL
        dest.source_url = raw.source_url

        # Tags.
        for tag_name, tag_category in parsed.get(
            "tags",
            [],
        ):
            result = await session.execute(
                select(Tag).where(
                    Tag.name == tag_name
                )
            )

            tag = (
                result.scalar_one_or_none()
            )

            if tag is None:
                tag = Tag(
                    name=tag_name,
                    category=tag_category,
                )

                session.add(tag)

                await session.flush()

            result = await session.execute(
                select(DestinationTag).where(
                    DestinationTag.destination_id
                    == dest.id,
                    DestinationTag.tag_id
                    == tag.id,
                )
            )

            existing_link = (
                result.scalar_one_or_none()
            )

            if existing_link is None:
                session.add(
                    DestinationTag(
                        destination_id=dest.id,
                        tag_id=tag.id,
                    )
                )

        raw.status = "published"

        await session.commit()
        await session.refresh(dest)

        return dest