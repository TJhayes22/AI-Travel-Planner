"""Shared ingestion utilities."""

from __future__ import annotations

import json
import re
from typing import Any


def normalize_parsed_data(
    raw_value: Any,
) -> dict[str, Any]:
    """Always return parsed_data as a dictionary."""

    if isinstance(raw_value, dict):
        return dict(raw_value)

    if isinstance(raw_value, str):
        text = raw_value.strip()

        if not text:
            return {}

        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return {"lead": text}

        if isinstance(parsed, dict):
            return parsed

        return {"lead": str(parsed)}

    return {}


def clean_wikitext_to_text(value: str) -> str:
    """Convert basic Wikivoyage wikitext into readable plain text."""

    text = value or ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove HTML comments.
    text = re.sub(
        r"<!--.*?-->",
        "",
        text,
        flags=re.DOTALL,
    )

    # Remove simple templates.
    # Repeat a few times because templates can be nested.
    for _ in range(3):
        new_text = re.sub(
            r"\{\{[^{}]*\}\}",
            "",
            text,
            flags=re.DOTALL,
        )

        if new_text == text:
            break

        text = new_text

    # Convert [[Target|Display text]] -> Display text
    text = re.sub(
        r"\[\[[^|\]]+\|([^\]]+)\]\]",
        r"\1",
        text,
    )

    # Convert [[Target]] -> Target
    text = re.sub(
        r"\[\[([^\]]+)\]\]",
        r"\1",
        text,
    )

    # Remove bold/italic markup.
    text = re.sub(
        r"'''''(.*?)'''''",
        r"\1",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"'''(.*?)'''",
        r"\1",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"''(.*?)''",
        r"\1",
        text,
        flags=re.DOTALL,
    )

    # Convert <br>, <br/>, <br /> to spaces.
    text = re.sub(
        r"<br\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    # Remove remaining HTML tags.
    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    # Remove common MediaWiki list markers.
    text = re.sub(
        r"^[*#:;]+\s*",
        "",
        text,
        flags=re.MULTILINE,
    )

    # Remove table markup.
    text = re.sub(
        r"^\{\|.*?$",
        "",
        text,
        flags=re.MULTILINE,
    )

    text = re.sub(
        r"^\|\}.*?$",
        "",
        text,
        flags=re.MULTILINE,
    )

    # Collapse whitespace.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    return text.strip()


def coerce_text(
    value: Any,
) -> str:
    """Convert a value into cleaned text."""

    if not isinstance(value, str):
        return ""

    return clean_wikitext_to_text(
        value
    )


def get_destination_summary(parsed: dict[str, Any]) -> str:
    """Return the best available destination description.

    Prefer the LLM-enriched description over raw Wikivoyage lead text.
    The raw lead is only used as a fallback when enrichment is unavailable.
    """
    for key in ("description", "summary", "lead"):
        text = coerce_text(parsed.get(key))
        if text:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for sentence in sentences:
                cleaned = sentence.strip().rstrip(". ")
                if cleaned and len(cleaned) > 20:
                    return cleaned[:600]
            return text[:600]

    sections = parsed.get("sections")
    if isinstance(sections, dict):
        for key in ("understand", "get in", "see", "do", "eat", "drink", "sleep", "history"):
            text = coerce_text(sections.get(key))
            if text:
                sentences = re.split(r"(?<=[.!?])\s+", text)
                for sentence in sentences:
                    cleaned = sentence.strip().rstrip(". ")
                    if cleaned and len(cleaned) > 20:
                        return cleaned[:600]
                return text[:600]

    return ""


def slug_to_display_name(
    slug: str,
) -> str:
    """Convert a destination slug into a display name."""

    return (
        slug
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )