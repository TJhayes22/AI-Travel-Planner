"""Fetch stage: pull Wikivoyage page wikitext and metadata."""

from __future__ import annotations

import hashlib
import os
from urllib.parse import quote

import httpx
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.destination import RawScrape


WIKIVOYAGE_API = (
    "https://en.wikivoyage.org/w/api.php"
)


async def fetch_title(title: str) -> RawScrape:
    """Fetch a Wikivoyage page and store its raw wikitext."""

    params = {
        "action": "query",
        "prop": "revisions|coordinates",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
        "formatversion": "2",
        "titles": title,
    }

    headers = {
        "User-Agent": (
            "AI-Travel-Planner/0.1 "
            "(https://github.com/TJhayes22/AI-Travel-Planner; "
            "tjhayes2224@gmail.com)"
        ),
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(
        timeout=30,
        headers=headers,
    ) as client:
        response = await client.get(
            WIKIVOYAGE_API,
            params=params,
        )

        response.raise_for_status()

        data = response.json()

    pages = (
        data
        .get("query", {})
        .get("pages", [])
    )

    if not pages:
        raise ValueError(
            f"No page found for {title}"
        )

    page = pages[0]

    if page.get("missing"):
        raise ValueError(
            f"Wikivoyage page missing: {title}"
        )

    revisions = page.get("revisions", [])

    if not revisions:
        raise ValueError(
            f"No revision found for {title}"
        )

    wikitext = (
        revisions[0]
        .get("slots", {})
        .get("main", {})
        .get("content", "")
    )

    if not wikitext:
        raise ValueError(
            f"Empty wikitext returned for {title}"
        )

    # Wikivoyage coordinates.
    coordinates = page.get("coordinates") or []

    latitude = None
    longitude = None

    if coordinates:
        latitude = coordinates[0].get("lat")
        longitude = coordinates[0].get("lon")

    source_url = (
        "https://en.wikivoyage.org/wiki/"
        + quote(title.replace(" ", "_"), safe="_-")
    )

    content_hash = hashlib.sha256(
        wikitext.encode("utf-8")
    ).hexdigest()

    backend_dir = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    cache_dir = os.path.join(
        backend_dir,
        "cache",
    )

    os.makedirs(
        cache_dir,
        exist_ok=True,
    )

    safe_filename = (
        title.replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )

    filename = os.path.join(
        cache_dir,
        f"{safe_filename}.wiki",
    )

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(wikitext)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RawScrape).where(
                RawScrape.source_url == source_url
            )
        )

        existing = (
            result.scalar_one_or_none()
        )

        if existing is None:
            raw = RawScrape(
                source_name="wikivoyage",
                source_url=source_url,
                s3_raw_key=filename,
                content_hash=content_hash,
                status="fetched",
                parsed_data={
                    "title": title,
                    "latitude": latitude,
                    "longitude": longitude,
                },
            )

            session.add(raw)

            await session.commit()
            await session.refresh(raw)

            return raw

        # Always preserve/update metadata from the current scrape.
        parsed = (
            existing.parsed_data
            if isinstance(existing.parsed_data, dict)
            else {}
        )

        parsed["title"] = title
        parsed["latitude"] = latitude
        parsed["longitude"] = longitude

        existing.parsed_data = parsed

        if existing.content_hash != content_hash:
            existing.s3_raw_key = filename
            existing.content_hash = content_hash
            existing.status = "fetched"

        await session.commit()
        await session.refresh(existing)

        return existing