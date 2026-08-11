"""Images stage: extract [[File:...]] references from wikitext, resolve them to
real, licensed image URLs via the Wikimedia Commons API, and attach them to a
destination via `destination_images`.

Wikitext image syntax is [[File:Name.jpg|options|caption]] ("Image:" is an
accepted alias for "File:") -- confirmed against MediaWiki's own documentation,
not guessed. This is the same syntax whether the file lives on Wikivoyage,
Wikipedia, or Commons directly.
"""
from __future__ import annotations

import os
import re
import sys
from typing import Any

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.destination import Destination, DestinationImage

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "AI-Travel-Planner/0.1 (contact: replace-with-your-real-contact@example.com)"

# Filenames matching these patterns are almost never good destination photos --
# flags, locator maps, coats of arms, generic UI icons that commonly appear in
# Wikivoyage/Wikipedia-style infoboxes alongside the real hero image.
EXCLUDE_PATTERNS = re.compile(
    r"(flag|locator|coat.?of.?arms|blank|icon|symbol|map\b|\.svg$)", re.IGNORECASE
)

FILE_REF_RE = re.compile(r"\[\[(?:File|Image):([^|\]]+)", re.IGNORECASE)


def scope_wikitext_for_images(wikitext: str) -> str:
    """Restricts raw wikitext down to the lead paragraph + the 'See' section
    before extracting image references. This is the fix for a real problem
    found on a live run: scanning the whole page pulls in images from
    unrelated content elsewhere on the page (e.g. a nearby town's market, an
    unrelated event mentioned in passing under "Do" or "Get in") -- the lead
    and "See" section are where genuinely representative destination photos
    actually live. Operates on RAW wikitext (not parse.py's cleaned output),
    since [[File:...]] links need to still be intact to extract from."""
    heading_match = re.search(r"^==\s*.+?\s*==\s*$", wikitext, flags=re.MULTILINE)
    lead = wikitext[: heading_match.start()] if heading_match else wikitext

    see_section = ""
    see_match = re.search(r"^==\s*See\s*==\s*$", wikitext, flags=re.MULTILINE | re.IGNORECASE)
    if see_match:
        start = see_match.end()
        next_heading = re.search(r"^==\s*.+?\s*==\s*$", wikitext[start:], flags=re.MULTILINE)
        end = start + next_heading.start() if next_heading else len(wikitext)
        see_section = wikitext[start:end]

    return lead + "\n" + see_section


def extract_file_references(wikitext: str, max_candidates: int = 4) -> list[str]:
    """Returns candidate image filenames in document order, deduplicated,
    with obvious non-photo files filtered out. Order matters -- the infobox
    image is typically referenced first, and we treat the first surviving
    candidate as the primary/hero image."""
    seen: set[str] = set()
    candidates: list[str] = []

    for match in FILE_REF_RE.finditer(wikitext):
        filename = match.group(1).strip()
        if not filename or filename in seen:
            continue
        seen.add(filename)
        if EXCLUDE_PATTERNS.search(filename):
            continue
        candidates.append(filename)
        if len(candidates) >= max_candidates:
            break

    return candidates


class ImageResolutionError(Exception):
    """Raised when Commons has no usable info for a filename (not necessarily
    fatal for the whole destination -- callers should skip and continue)."""


async def resolve_image_info(filenames: list[str], client: httpx.AsyncClient) -> dict[str, dict]:
    """Resolves a batch of Commons filenames to their real URL + license info
    in ONE API call. Returns {filename: {"url": ..., "license": ..., "artist": ...}}
    -- missing/unusable files are simply absent from the result, not raised as
    errors, since a single bad filename shouldn't break the whole batch."""
    if not filenames:
        return {}

    titles = "|".join(f"File:{name}" for name in filenames)
    params = {
        "action": "query",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime",
        "format": "json",
        "formatversion": "2",
        "titles": titles,
    }

    resp = await client.get(COMMONS_API, params=params)
    resp.raise_for_status()
    data = resp.json()

    results: dict[str, dict] = {}
    for page in data.get("query", {}).get("pages", []):
        if page.get("missing"):
            continue
        title = page.get("title", "")
        filename = title.replace("File:", "", 1)
        imageinfo = page.get("imageinfo", [])
        if not imageinfo:
            continue
        info = imageinfo[0]
        mime = info.get("mime", "")
        if not mime.startswith("image/"):
            continue  # skip non-image files (e.g. audio pronunciation clips)

        extmeta = info.get("extmetadata", {})
        license_name = extmeta.get("LicenseShortName", {}).get("value", "unknown")
        artist_raw = extmeta.get("Artist", {}).get("value", "")
        artist = re.sub(r"<[^>]+>", "", artist_raw).strip() or "unknown"

        results[filename] = {
            "url": info.get("url", ""),
            # CC attribution convention: link to the file's page (full license
            # context), not the bare CDN image URL -- that goes in s3_key instead.
            "commons_page_url": f"https://commons.wikimedia.org/wiki/File:{filename}",
            "license": license_name,
            "artist": artist,
        }

    return results


async def attach_images_to_destination(
    destination_id: Any, wikitext: str, client: httpx.AsyncClient | None = None
) -> int:
    """Extracts, resolves, and attaches images for one destination. Returns the
    number of images successfully attached. Safe to call on a destination that
    already has images -- existing ones (matched by s3_key/URL) are left alone,
    not duplicated."""
    candidates = extract_file_references(scope_wikitext_for_images(wikitext))
    if not candidates:
        return 0

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=30, headers={"User-Agent": USER_AGENT})

    try:
        resolved = await resolve_image_info(candidates, client)
    finally:
        if owns_client:
            await client.aclose()

    if not resolved:
        return 0

    from sqlalchemy import select

    attached = 0
    async with AsyncSessionLocal() as session:
        existing_result = await session.execute(
            select(DestinationImage.s3_key).where(
                DestinationImage.destination_id == destination_id
            )
        )
        existing_urls = {row[0] for row in existing_result.all()}

        has_primary_result = await session.execute(
            select(DestinationImage).where(
                DestinationImage.destination_id == destination_id,
                DestinationImage.is_primary.is_(True),
            )
        )
        has_primary = has_primary_result.scalar_one_or_none() is not None

        sort_order = 0
        # Iterate in the original candidate order, not dict order, so the
        # infobox/primary image stays first.
        for filename in candidates:
            info = resolved.get(filename)
            if info is None:
                continue
            if info["url"] in existing_urls:
                continue

            image = DestinationImage(
                destination_id=destination_id,
                s3_key=info["url"],
                alt_text=filename.rsplit(".", 1)[0].replace("_", " "),
                source_url=info["commons_page_url"],
                source_name="wikimedia_commons",
                attribution=f"{info['artist']}, {info['license']}"[:500],
                is_primary=(not has_primary and attached == 0),
                sort_order=sort_order,
            )
            session.add(image)
            attached += 1
            sort_order += 1
            if not has_primary and attached == 1:
                has_primary = True

        await session.commit()

    return attached


async def attach_images_for_raw_scrape(raw_scrape_id: Any, destination_id: Any) -> int:
    """Convenience wrapper: loads the cached wikitext for a raw_scrape (already
    fetched by fetch.py) and attaches its images to the given destination."""
    from app.models.destination import RawScrape

    async with AsyncSessionLocal() as session:
        raw = await session.get(RawScrape, raw_scrape_id)
        if raw is None or not os.path.exists(raw.s3_raw_key):
            return 0
        with open(raw.s3_raw_key, "r", encoding="utf-8") as fh:
            wikitext = fh.read()

    return await attach_images_to_destination(destination_id, wikitext)