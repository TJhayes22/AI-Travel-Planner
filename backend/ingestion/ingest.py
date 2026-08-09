"""Orchestrator for the ingestion pipeline.

Usage (from backend/):

    python -m ingestion.ingest --titles "Paris" "Tokyo"

Dry run:

    python -m ingestion.ingest --titles "Paris" "Tokyo" --dry-run

A dry run still fetches, parses, enriches, and publishes destinations.
The only stage skipped externally is the embedding API call; embeddings
are replaced with zero vectors.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import List

from ingestion.embed import embed_raw_scrapes_batch
from ingestion.enrich import enrich_raw_scrape
from ingestion.fetch import fetch_title
from ingestion.parse import parse_raw_scrape
from ingestion.publish import publish_raw_scrape


async def ingest_title(title: str) -> object:
    """Fetch, parse, and enrich one destination.

    Embedding is deliberately not done here because embeddings are batched
    across all titles after every destination has been enriched.
    """
    print(f"-- ingest: {title}")

    raw = await fetch_title(title)
    print(f"  fetched: {title}")

    raw = await parse_raw_scrape(raw.id)
    print(f"  parsed: {title}")

    raw = await enrich_raw_scrape(raw.id)
    print(f"  enriched: {title}")

    return raw


async def _main_async(args: argparse.Namespace) -> None:
    # Fetch/parse/enrich all destinations concurrently.
    raws = await asyncio.gather(
        *(ingest_title(title) for title in args.titles)
    )

    raw_ids = [raw.id for raw in raws]

    print(f"\n-- embedding {len(raw_ids)} destinations in one batch")

    # ONE embedding API request for all destinations.
    embedded_raws = await embed_raw_scrapes_batch(
        raw_ids,
        dry_run=args.dry_run,
    )

    print("-- embedding complete")

    # Publish after embeddings have been saved.
    for raw in embedded_raws:
        dest = await publish_raw_scrape(raw.id)
        print(f"  published: {dest.slug}")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run the travel destination ingestion pipeline."
    )

    parser.add_argument(
        "--titles",
        nargs="+",
        required=True,
        help="Wikivoyage destination titles to ingest.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use zero-vector embeddings instead of calling the embedding API.",
    )

    args = parser.parse_args(argv)

    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()