"""Embed stage: generate embeddings for enriched destination data.

All destinations are embedded in a single batched API request by the
orchestrator. This avoids making one embedding request per destination.
"""

from __future__ import annotations

from typing import Any

from app.db.session import AsyncSessionLocal
from app.models.destination import RawScrape
from app.config import get_settings
from ingestion.utils import normalize_parsed_data


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def build_embedding_text(parsed: dict[str, Any]) -> str:
    """Build consistent structured text for embedding."""

    title = parsed.get("title", "")
    description = parsed.get("description", "")
    climate = parsed.get("climate", "")
    best_season = parsed.get("best_season", "")
    country = parsed.get("country", "")
    region = parsed.get("region", "")

    tag_names = ", ".join(
        name for name, _ in parsed.get("tags", [])
    )

    return (
        f"{title}, {country}"
        f"{f', {region}' if region else ''}. "
        f"{description} "
        f"Climate: {climate}. "
        f"Best time to visit: {best_season}. "
        f"Tags: {tag_names}."
    )


async def get_embeddings(
    texts: list[str],
    dry_run: bool = False,
) -> list[list[float]]:
    """Generate embeddings for multiple texts."""

    if not texts:
        return []

    if dry_run:
        return [
            [0.0] * EMBEDDING_DIM
            for _ in texts
        ]

    from openai import AsyncOpenAI

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    # OpenAI returns embeddings in the same order as the inputs.
    return [item.embedding for item in response.data]


async def embed_raw_scrapes_batch(
    raw_scrape_ids: list[Any],
    dry_run: bool = False,
) -> list[RawScrape]:
    """Embed and save multiple RawScrape records in one batch."""

    if not raw_scrape_ids:
        return []

    async with AsyncSessionLocal() as session:
        raws: list[RawScrape] = []

        for raw_scrape_id in raw_scrape_ids:
            raw = await session.get(RawScrape, raw_scrape_id)

            if raw is None:
                raise ValueError(
                    f"raw_scrape not found: {raw_scrape_id}"
                )

            raws.append(raw)

        texts = [
            build_embedding_text(
                normalize_parsed_data(raw.parsed_data)
            )
            for raw in raws
        ]

        embeddings = await get_embeddings(
            texts,
            dry_run=dry_run,
        )

        if len(embeddings) != len(raws):
            raise RuntimeError(
                "Embedding API returned a different number of embeddings "
                f"({len(embeddings)}) than inputs ({len(raws)})."
            )

        for raw, embedding in zip(raws, embeddings):
            parsed = normalize_parsed_data(raw.parsed_data)

            parsed["embedding"] = embedding
            parsed["embedding_model"] = (
                EMBEDDING_MODEL
                if not dry_run
                else "dry-run-zero-vector"
            )

            raw.parsed_data = parsed

            # Keep the existing status convention.
            # publish.py changes it to "published".
            raw.status = "enriched"

        await session.commit()

        for raw in raws:
            await session.refresh(raw)

        return raws