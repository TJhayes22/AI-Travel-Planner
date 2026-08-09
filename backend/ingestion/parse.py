"""Parse stage: extract useful text from cached Wikivoyage wikitext."""

from __future__ import annotations

import os
import re
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.destination import RawScrape
from ingestion.utils import clean_wikitext_to_text, normalize_parsed_data


RELEVANT_SECTIONS = (
    "understand",
    "climate",
    "get in",
    "see",
    "do",
    "buy",
    "eat",
    "drink",
    "sleep",
)


def extract_sections(wikitext: str) -> tuple[str, dict[str, str]]:
    """Extract the lead and relevant top-level sections."""

    # Find the first level-2 heading.
    first_heading = re.search(
        r"^==\s*.+?\s*==\s*$",
        wikitext,
        flags=re.MULTILINE,
    )

    if first_heading:
        lead_source = wikitext[: first_heading.start()]
    else:
        lead_source = wikitext

    lead = clean_wikitext_to_text(lead_source)

    sections: dict[str, str] = {}

    # Find all level-2 headings.
    headings = list(
        re.finditer(
            r"^==\s*(.+?)\s*==\s*$",
            wikitext,
            flags=re.MULTILINE,
        )
    )

    for index, match in enumerate(headings):
        header = match.group(1).strip().lower()

        if header not in RELEVANT_SECTIONS:
            continue

        start = match.end()

        if index + 1 < len(headings):
            end = headings[index + 1].start()
        else:
            end = len(wikitext)

        section_text = wikitext[start:end]
        cleaned = clean_wikitext_to_text(section_text)

        if cleaned:
            sections[header] = cleaned[:1200]

    return lead[:2000], sections


async def parse_raw_scrape(raw_scrape_id: Any) -> RawScrape:
    async with AsyncSessionLocal() as session:
        raw = await session.get(RawScrape, raw_scrape_id)

        if raw is None:
            raise ValueError("raw_scrape not found")

        if not raw.s3_raw_key:
            raise ValueError(
                f"Raw scrape {raw_scrape_id} has no cached file path"
            )

        if not os.path.exists(raw.s3_raw_key):
            raise FileNotFoundError(
                f"Cached file not found: {raw.s3_raw_key}"
            )

        with open(raw.s3_raw_key, "r", encoding="utf-8") as fh:
            wikitext = fh.read()

        lead, sections = extract_sections(wikitext)

        # IMPORTANT:
        # Build a completely new dictionary so SQLAlchemy definitely
        # sees the JSONB value as changed.
        old_parsed = normalize_parsed_data(raw.parsed_data)

        parsed = {
            **old_parsed,
            "title": old_parsed.get("title") or raw.source_url.rstrip("/").split("/")[-1].replace("_", " "),
            "lead": lead,
            "sections": sections,
        }

        raw.parsed_data = parsed
        raw.status = "parsed"

        print(
            f"  parsed content: "
            f"lead={len(lead)} chars, "
            f"sections={list(sections.keys())}"
        )

        print(
            f"  saving parsed_data keys: {list(parsed.keys())}"
        )

        await session.commit()

        # Re-read the row from the database.
        await session.refresh(raw)

        saved_parsed = normalize_parsed_data(raw.parsed_data)

        print(
            f"  verified DB parsed_data keys: "
            f"{list(saved_parsed.keys())}"
        )

        return raw