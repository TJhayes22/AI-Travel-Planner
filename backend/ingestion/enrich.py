"""Enrich stage: use an LLM to turn parsed Wikivoyage content into structured
destination data.

The enrichment stage produces:
- description
- country
- region
- climate
- best_season
- cost_tier
- tags

The real OpenAI call is used by default. Tests can inject a fake llm_call.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ),
)

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.destination import RawScrape
from ingestion.utils import normalize_parsed_data


ENRICH_MODEL = "gpt-4o-mini"

ALLOWED_TAG_CATEGORIES = {
    "vibe",
    "activity",
    "climate",
    "cost",
    "other",
}


SYSTEM_PROMPT = """
You are extracting structured travel-destination data from a Wikivoyage
article for a travel recommendation database.

Given the article's title, lead paragraph, and selected sections, respond with
ONLY a valid JSON object. Do not include Markdown, explanations, commentary,
or code fences.

The JSON object must contain exactly these fields:

{
  "description": "A specific 45-80 word travel-planning summary",
  "country": "country this destination is located in",
  "region": "state/province/prefecture/region, or null if not identifiable",
  "climate": "brief climate description",
  "best_season": "best time of year to visit",
  "cost_tier": 1,
  "tags": [
    ["culture", "vibe"],
    ["hiking", "activity"],
    ["budget-friendly", "cost"]
  ]
}

DESCRIPTION REQUIREMENTS:

The description will be displayed directly on a travel-planning website.
It should help a traveler understand what makes the destination worth
considering and what they can actually experience there.

Write approximately 45-80 words in 2-3 sentences.

Prioritize concrete, destination-specific information such as:
- Major attractions or landmarks
- Historic districts or notable neighborhoods
- Local food or culinary experiences
- Architecture
- Beaches, mountains, landscapes, or other natural features
- Outdoor activities
- Cultural experiences
- Markets, festivals, nightlife, or entertainment
- The overall type of travel experience the destination offers

Use specific details from the provided Wikivoyage content whenever possible.

For example, prefer:
"Marrakech centers around its historic medina, where narrow streets lead
through busy souks, traditional riads, food stalls, and historic palaces.
The city is particularly suited to travelers interested in Moroccan
architecture, cuisine, markets, and culture, while the nearby Atlas Mountains
offer opportunities for day trips and outdoor excursions."

Avoid vague descriptions such as:
"X is a vibrant city known for its rich history and culture."

Avoid generic phrases that could describe many destinations, including:
- "rich history and culture"
- "blend of traditional and modern culture"
- "vibrant city"
- "beautiful destination"
- "stunning scenery"
- "something for everyone"
- "popular tourist destination"
- "unique blend of..."
unless they are immediately supported by specific details.

Do not use empty marketing language or exaggerated claims.
Do not simply restate the article's opening sentence.
Do not write a Wikipedia-style definition.
Do not repeat the destination name unnecessarily.
Do not invent specific attractions, statistics, events, or other factual
claims that are not reasonably supported by the source or established
general knowledge.
Do not use generic statements and promotional phrases such as 'don't miss,' 'must-see,' or 'world-class' unless they are directly relevant and factual.

The description should be factual, concise, and useful for someone deciding
whether the destination fits their travel interests.

COUNTRY AND REGION:

Identify the country where the destination is located.

For "region", use the appropriate administrative or commonly recognized
region, such as a state, province, prefecture, department, territory, or
similar subdivision.

If the region cannot be identified reliably, return null.

CLIMATE:

Provide a concise description of the destination's typical climate.
Include useful characteristics such as hot/cold seasons, rainfall,
humidity, dry seasons, or notable seasonal differences when relevant.

BEST SEASON:

Provide a concise recommendation for the best time of year to visit based
on weather, climate, and typical travel conditions.

COST TIER:

cost_tier must be an integer from 1 to 5:

1 = very budget-friendly
2 = budget-friendly
3 = moderate
4 = expensive
5 = very expensive

Base the cost tier on the typical cost of accommodation, food,
transportation, and activities for a traveler.

TAGS:

Tags must contain 3-6 [name, category] pairs.

Each category must be exactly one of:

"vibe"
"activity"
"climate"
"cost"
"other"

Tag names should be short, lowercase, single words or hyphenated words.

Choose tags that meaningfully describe the destination and help match it
with traveler preferences.

Prefer specific tags such as:
["street-food", "food"]
["nightlife", "vibe"]
["hiking", "activity"]
["beaches", "activity"]
["architecture", "vibe"]
["historic", "vibe"]
["budget-friendly", "cost"]

Do not generate generic tags that provide little recommendation value.

SOURCE RELIABILITY:

Use the provided Wikivoyage content as the primary source of information.

If the source content does not explicitly provide a field, you may use
established general knowledge to fill the field when necessary. Do not
invent specific factual details simply to make the response more complete.

If information is genuinely unavailable or cannot be determined reliably,
use null where the schema permits it.

OUTPUT:

Return ONLY the JSON object.

The response must contain exactly these fields:
"description",
"country",
"region",
"climate",
"best_season",
"cost_tier",
"tags".

Do not add additional fields.
"""


class EnrichmentError(Exception):
    """Raised when the LLM response cannot be parsed or validated."""


def build_user_prompt(
    title: str,
    lead: str,
    sections: dict[str, str],
) -> str:
    """Build the user prompt sent to the LLM."""

    parts = [
        f"Title: {title}",
        f"Lead: {lead}",
    ]

    for name, text in sections.items():
        parts.append(
            f"\n[{name.title()}]\n{text}"
        )

    return "\n".join(parts)


def validate_enrichment(
    data: dict[str, Any],
) -> dict[str, Any]:
    """Validate and normalize the LLM response."""

    if not isinstance(data, dict):
        raise EnrichmentError(
            "LLM response was not a JSON object"
        )

    description = str(
        data.get("description", "")
    ).strip()

    if not description:
        raise EnrichmentError(
            "LLM response missing required "
            "'description' field"
        )

    country = str(
        data.get("country", "")
    ).strip()

    if not country:
        raise EnrichmentError(
            "LLM response missing required "
            "'country' field"
        )

    # Normalize cost tier.
    cost_tier = data.get(
        "cost_tier",
        3,
    )

    try:
        cost_tier = int(cost_tier)
    except (TypeError, ValueError):
        cost_tier = 3

    cost_tier = max(
        1,
        min(5, cost_tier),
    )

    # Normalize tags.
    raw_tags = data.get(
        "tags",
        [],
    )

    tags: list[tuple[str, str]] = []

    if isinstance(raw_tags, list):
        for item in raw_tags:

            if not isinstance(
                item,
                (list, tuple),
            ):
                continue

            if len(item) != 2:
                continue

            name, category = item

            name = str(
                name
            ).strip().lower()

            category = str(
                category
            ).strip().lower()

            if (
                name
                and category
                in ALLOWED_TAG_CATEGORIES
            ):
                tags.append(
                    (name, category)
                )

    return {
        "description": description[:600],
        "country": country,
        "region": (
            str(data["region"]).strip()
            if data.get("region")
            else None
        ),
        "climate": (
            str(data["climate"]).strip()
            if data.get("climate")
            else None
        ),
        "best_season": (
            str(data["best_season"]).strip()
            if data.get("best_season")
            else None
        ),
        "cost_tier": cost_tier,
        "tags": tags[:6],
    }


async def call_llm_openai(
    title: str,
    lead: str,
    sections: dict[str, str],
) -> dict[str, Any]:
    """Call OpenAI asynchronously."""

    from openai import AsyncOpenAI

    settings = get_settings()
    if not settings.openai_api_key:
        raise EnrichmentError("OPENAI_API_KEY is not set")

    client = AsyncOpenAI(
        api_key=settings.openai_api_key
    )

    response = await client.chat.completions.create(
        model=ENRICH_MODEL,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_user_prompt(
                    title,
                    lead,
                    sections,
                ),
            },
        ],
        temperature=0.3,
    )

    content = (
        response.choices[0]
        .message
        .content
    )

    if not content:
        raise EnrichmentError(
            "OpenAI returned an empty response"
        )

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise EnrichmentError(
            f"OpenAI returned invalid JSON: {exc}"
        ) from exc


async def enrich_raw_scrape(
    raw_scrape_id: Any,
    llm_call: Callable[
        [str, str, dict[str, str]],
        Awaitable[dict[str, Any]],
    ] = call_llm_openai,
) -> RawScrape:
    """Enrich one parsed RawScrape using an LLM."""

    async with AsyncSessionLocal() as session:

        raw = await session.get(
            RawScrape,
            raw_scrape_id,
        )

        if raw is None:
            raise ValueError(
                f"raw_scrape not found: "
                f"{raw_scrape_id}"
            )

        # Normalize the JSON data stored in the DB.
        parsed = normalize_parsed_data(
            raw.parsed_data
        )

        # Debug information. This is intentionally
        # useful while we're fixing the pipeline.
        print(
            f"  enriching: {raw_scrape_id}"
        )
        print(
            f"  parsed keys: "
            f"{list(parsed.keys())}"
        )

        title = str(
            parsed.get(
                "title",
                "",
            )
        ).strip()

        lead = str(
            parsed.get(
                "lead",
                "",
            )
        ).strip()

        sections_raw = parsed.get(
            "sections",
            {},
        )

        if isinstance(
            sections_raw,
            dict,
        ):
            sections = {
                str(key): str(value)
                for key, value
                in sections_raw.items()
                if value
            }
        else:
            sections = {}

        print(
            f"  enrichment input: "
            f"title={title!r}, "
            f"lead={len(lead)} chars, "
            f"sections={list(sections.keys())}"
        )

        if not lead and not sections:
            raise EnrichmentError(
                "No parsed content available for "
                f"raw_scrape {raw_scrape_id}. "
                f"Parsed keys were: "
                f"{list(parsed.keys())}"
            )

        # Call the injected LLM function.
        llm_response = await llm_call(
            title,
            lead,
            sections,
        )

        validated = validate_enrichment(
            llm_response
        )

        # Add the enriched fields while preserving
        # the title, coordinates, lead, sections, etc.
        parsed.update(validated)

        parsed["enriched_at"] = datetime.now(timezone.utc).isoformat()

        raw.parsed_data = dict(parsed)
        raw.status = "enriched"

        await session.commit()
        await session.refresh(raw)

        print(
            f"  enriched: "
            f"{title or raw_scrape_id}"
        )

        return raw