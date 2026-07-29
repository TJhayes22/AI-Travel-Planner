"""
Seed script — populates the destinations table with a small, hand-picked set of
real destinations, each with a genuine OpenAI embedding.

Usage:
    python scripts/seed_destinations.py            # real embeddings via OpenAI
    python scripts/seed_destinations.py --dry-run   # fake embeddings, no API calls, no cost

Safe to re-run: existing destinations (matched by slug) are skipped, not duplicated.
Run this from the `backend/` directory so it can import `app.*` and read `.env`.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

# Ensure `backend/` (this script's parent directory) is on sys.path, so
# `app.*` imports resolve whether this is run as `python scripts/seed_destinations.py`
# from within backend/, or invoked from elsewhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.destination import Destination
from app.models.tag import DestinationTag, Tag

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# ----------------------------------------------------------------------------
# Seed data — a deliberately varied set (beach, city, culture, adventure,
# budget/luxury) so search results are actually meaningful to test later.
# tags: list of (name, category) — category must be one of:
#   'vibe' | 'activity' | 'climate' | 'cost' | 'other'
# ----------------------------------------------------------------------------

DESTINATIONS: list[dict] = [
    {
        "name": "Kyoto",
        "slug": "kyoto-japan",
        "country": "Japan",
        "region": "Kansai",
        "latitude": 35.0116,
        "longitude": 135.7681,
        "description": (
            "Historic former capital known for thousands of Buddhist temples, "
            "traditional wooden machiya houses, and meticulously kept gardens. "
            "A calm, culturally rich city best explored slowly and on foot."
        ),
        "cost_tier": 3,
        "climate": "temperate, four distinct seasons",
        "best_season": "spring (cherry blossoms) or autumn (fall foliage)",
        "tags": [("culture", "vibe"), ("temples", "activity"), ("walkable", "vibe")],
    },
    {
        "name": "Bali",
        "slug": "bali-indonesia",
        "country": "Indonesia",
        "region": "Lesser Sunda Islands",
        "latitude": -8.3405,
        "longitude": 115.0920,
        "description": (
            "Tropical island known for surf beaches, terraced rice paddies, "
            "and a strong wellness/retreat culture. Popular with digital nomads "
            "and long-stay travelers for its affordability and laid-back pace."
        ),
        "cost_tier": 2,
        "climate": "tropical, warm and humid year-round",
        "best_season": "April to October (dry season)",
        "tags": [("beach", "vibe"), ("wellness", "activity"), ("budget-friendly", "cost")],
    },
    {
        "name": "Reykjavik",
        "slug": "reykjavik-iceland",
        "country": "Iceland",
        "region": "Capital Region",
        "latitude": 64.1466,
        "longitude": -21.9426,
        "description": (
            "Small, walkable capital that serves as the gateway to Iceland's "
            "dramatic landscapes: glaciers, waterfalls, geothermal springs, and "
            "the northern lights in winter. A base for adventure and road trips."
        ),
        "cost_tier": 5,
        "climate": "subarctic, cold and windy",
        "best_season": "June to August for daylight, Sept-March for northern lights",
        "tags": [("adventure", "vibe"), ("nature", "activity"), ("luxury", "cost")],
    },
    {
        "name": "Lisbon",
        "slug": "lisbon-portugal",
        "country": "Portugal",
        "region": "Lisbon District",
        "latitude": 38.7223,
        "longitude": -9.1393,
        "description": (
            "Hilly coastal capital with colorful tiled buildings, historic trams, "
            "and a lively food and nightlife scene. Increasingly popular with remote "
            "workers for its affordability relative to other Western European capitals."
        ),
        "cost_tier": 2,
        "climate": "Mediterranean, mild winters and warm summers",
        "best_season": "March to May or September to October",
        "tags": [("nightlife", "vibe"), ("food", "activity"), ("budget-friendly", "cost")],
    },
    {
        "name": "Queenstown",
        "slug": "queenstown-new-zealand",
        "country": "New Zealand",
        "region": "Otago",
        "latitude": -45.0312,
        "longitude": 168.6626,
        "description": (
            "Alpine resort town on Lake Wakatipu, considered the adventure sports "
            "capital of the world: bungee jumping, skiing, hiking, and jet boating "
            "against a backdrop of dramatic mountains."
        ),
        "cost_tier": 4,
        "climate": "temperate, four distinct seasons with snowy winters",
        "best_season": "December to February (summer) or June to August (ski season)",
        "tags": [("adventure", "vibe"), ("skiing", "activity"), ("nature", "activity")],
    },
    {
        "name": "Mexico City",
        "slug": "mexico-city-mexico",
        "country": "Mexico",
        "region": "CDMX",
        "latitude": 19.4326,
        "longitude": -99.1332,
        "description": (
            "Massive, culturally dense capital with world-class museums, ancient "
            "Aztec ruins, and one of the best food scenes in the Americas. "
            "Vibrant, chaotic, and endlessly walkable neighborhood by neighborhood."
        ),
        "cost_tier": 2,
        "climate": "subtropical highland, mild year-round due to elevation",
        "best_season": "March to May",
        "tags": [("food", "activity"), ("culture", "vibe"), ("big-city", "vibe")],
    },
    {
        "name": "Santorini",
        "slug": "santorini-greece",
        "country": "Greece",
        "region": "Cyclades",
        "latitude": 36.3932,
        "longitude": 25.4615,
        "description": (
            "Iconic volcanic island with whitewashed, blue-domed villages perched "
            "on cliffs above the Aegean Sea. Known for dramatic sunsets, wineries, "
            "and a romantic, upscale atmosphere."
        ),
        "cost_tier": 4,
        "climate": "Mediterranean, hot dry summers",
        "best_season": "late May to early June, or September",
        "tags": [("beach", "vibe"), ("romantic", "vibe"), ("luxury", "cost")],
    },
    {
        "name": "Chiang Mai",
        "slug": "chiang-mai-thailand",
        "country": "Thailand",
        "region": "Northern Thailand",
        "latitude": 18.7883,
        "longitude": 98.9853,
        "description": (
            "Laid-back northern Thai city surrounded by mountains and jungle, "
            "known for its old-town temples, night markets, and a large community "
            "of long-term digital nomads drawn by the low cost of living."
        ),
        "cost_tier": 1,
        "climate": "tropical, hot with a cooler dry season",
        "best_season": "November to February",
        "tags": [("budget-friendly", "cost"), ("culture", "vibe"), ("temples", "activity")],
    },
    {
        "name": "Banff",
        "slug": "banff-canada",
        "country": "Canada",
        "region": "Alberta",
        "latitude": 51.1784,
        "longitude": -115.5708,
        "description": (
            "Mountain town inside Banff National Park, surrounded by turquoise "
            "glacial lakes, dramatic peaks, and extensive hiking and skiing terrain. "
            "A classic base for outdoor-focused trips."
        ),
        "cost_tier": 4,
        "climate": "alpine, cold snowy winters and mild summers",
        "best_season": "June to September (hiking) or December to March (skiing)",
        "tags": [("nature", "activity"), ("skiing", "activity"), ("adventure", "vibe")],
    },
    {
        "name": "Marrakech",
        "slug": "marrakech-morocco",
        "country": "Morocco",
        "region": "Marrakech-Safi",
        "latitude": 31.6295,
        "longitude": -7.9811,
        "description": (
            "Historic imperial city built around a maze-like medina, bustling "
            "souks, and ornate riads. A sensory-heavy destination known for its "
            "markets, food, and easy access to the nearby Atlas Mountains."
        ),
        "cost_tier": 2,
        "climate": "semi-arid, hot summers and mild winters",
        "best_season": "March to May or September to November",
        "tags": [("culture", "vibe"), ("food", "activity"), ("budget-friendly", "cost")],
    },
    {
        "name": "Copenhagen",
        "slug": "copenhagen-denmark",
        "country": "Denmark",
        "region": "Capital Region",
        "latitude": 55.6761,
        "longitude": 12.5683,
        "description": (
            "Bike-friendly Scandinavian capital known for its design culture, "
            "New Nordic cuisine, and a high quality of life. Compact, walkable, "
            "and calm compared to other major European capitals."
        ),
        "cost_tier": 5,
        "climate": "oceanic, mild summers and cool winters",
        "best_season": "May to August",
        "tags": [("food", "activity"), ("walkable", "vibe"), ("luxury", "cost")],
    },
    {
        "name": "Cartagena",
        "slug": "cartagena-colombia",
        "country": "Colombia",
        "region": "Bolivar",
        "latitude": 10.3910,
        "longitude": -75.4794,
        "description": (
            "Colorful Caribbean coastal city with a walled colonial old town, "
            "vibrant nightlife, and nearby beaches and islands. Warm year-round "
            "and increasingly popular for both tourism and long stays."
        ),
        "cost_tier": 2,
        "climate": "tropical, hot and humid year-round",
        "best_season": "December to March (drier season)",
        "tags": [("beach", "vibe"), ("nightlife", "vibe"), ("budget-friendly", "cost")],
    },
    {
        "name": "Vienna",
        "slug": "vienna-austria",
        "country": "Austria",
        "region": "Vienna",
        "latitude": 48.2082,
        "longitude": 16.3738,
        "description": (
            "Grand imperial capital known for classical music, palatial "
            "architecture, coffeehouse culture, and world-class museums. "
            "Consistently ranked among the most livable cities in the world."
        ),
        "cost_tier": 4,
        "climate": "temperate, four distinct seasons",
        "best_season": "April to June or September to October",
        "tags": [("culture", "vibe"), ("walkable", "vibe"), ("food", "activity")],
    },
    {
        "name": "Ubud",
        "slug": "ubud-indonesia",
        "country": "Indonesia",
        "region": "Bali",
        "latitude": -8.5069,
        "longitude": 115.2625,
        "description": (
            "Inland Balinese town surrounded by rice terraces and jungle, known "
            "as the island's cultural and wellness center: yoga retreats, art "
            "markets, and a quieter pace than the coastal beach towns."
        ),
        "cost_tier": 1,
        "climate": "tropical, warm and humid year-round",
        "best_season": "April to October (dry season)",
        "tags": [("wellness", "activity"), ("nature", "activity"), ("budget-friendly", "cost")],
    },
    {
        "name": "Edinburgh",
        "slug": "edinburgh-scotland",
        "country": "United Kingdom",
        "region": "Scotland",
        "latitude": 55.9533,
        "longitude": -3.1883,
        "description": (
            "Historic hilltop city dominated by its medieval castle, known for "
            "dramatic architecture, a famous arts festival, and easy access to "
            "the Scottish Highlands for day trips."
        ),
        "cost_tier": 3,
        "climate": "oceanic, cool and often overcast",
        "best_season": "May to September",
        "tags": [("culture", "vibe"), ("walkable", "vibe"), ("nature", "activity")],
    },
]


def build_embedding_text(dest: dict) -> str:
    """Builds the text used to generate the embedding for a destination.
    Keeping this consistent and structured (not just raw description) gives
    more reliable, comparable embeddings across destinations."""
    tag_names = ", ".join(t[0] for t in dest["tags"])
    return (
        f"{dest['name']}, {dest['country']}. {dest['description']} "
        f"Climate: {dest['climate']}. Best time to visit: {dest['best_season']}. "
        f"Tags: {tag_names}."
    )


def get_embeddings(texts: list[str], dry_run: bool) -> list[list[float]]:
    """Fetches embeddings for all texts in a single batched API call.
    In --dry-run mode, returns zero-vectors instead of calling OpenAI."""
    if dry_run:
        print(f"[dry-run] Skipping OpenAI call, generating {len(texts)} zero-vectors.")
        return [[0.0] * EMBEDDING_DIM for _ in texts]

    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    print(f"Calling OpenAI ({EMBEDDING_MODEL}) for {len(texts)} destinations in one batch...")
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    # response.data is returned in the same order as the input list
    return [item.embedding for item in response.data]


async def get_or_create_tag(session, name: str, category: str) -> Tag:
    result = await session.execute(select(Tag).where(Tag.name == name))
    tag = result.scalar_one_or_none()
    if tag is None:
        tag = Tag(name=name, category=category)
        session.add(tag)
        await session.flush()  # get tag.id without a full commit
    return tag


async def seed(dry_run: bool) -> None:
    texts = [build_embedding_text(dest) for dest in DESTINATIONS]
    embeddings = get_embeddings(texts, dry_run=dry_run)

    inserted = 0
    skipped = 0

    async with AsyncSessionLocal() as session:
        for dest, embedding in zip(DESTINATIONS, embeddings):
            existing = await session.execute(
                select(Destination).where(Destination.slug == dest["slug"])
            )
            if existing.scalar_one_or_none() is not None:
                print(f"  skip (already exists): {dest['slug']}")
                skipped += 1
                continue

            destination = Destination(
                name=dest["name"],
                slug=dest["slug"],
                country=dest["country"],
                region=dest["region"],
                latitude=dest["latitude"],
                longitude=dest["longitude"],
                description=dest["description"],
                cost_tier=dest["cost_tier"],
                climate=dest["climate"],
                best_season=dest["best_season"],
                status="published",
                embedding=embedding,
                embedding_model="dry-run-zero-vector" if dry_run else EMBEDDING_MODEL,
                embedding_updated_at=datetime.now(timezone.utc),
            )
            session.add(destination)
            await session.flush()  # get destination.id for the tag links below

            for tag_name, tag_category in dest["tags"]:
                tag = await get_or_create_tag(session, tag_name, tag_category)
                session.add(DestinationTag(destination_id=destination.id, tag_id=tag.id))

            print(f"  inserted: {dest['slug']}")
            inserted += 1

        await session.commit()

    print(f"\nDone. Inserted: {inserted}, skipped (already existed): {skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use fake zero-vectors instead of calling the OpenAI API (no cost).",
    )
    args = parser.parse_args()

    if not args.dry_run:
        confirm = input(
            f"This will call the OpenAI API ({EMBEDDING_MODEL}) for "
            f"{len(DESTINATIONS)} destinations in a single batched request. "
            f"Estimated cost: well under $0.01. Continue? [y/N] "
        )
        if confirm.strip().lower() != "y":
            print("Aborted.")
            sys.exit(0)

    asyncio.run(seed(dry_run=args.dry_run))


if __name__ == "__main__":
    main()