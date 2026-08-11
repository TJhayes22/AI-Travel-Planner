"""Orchestrator for the ingestion pipeline.

Usage (from backend/):
    python -m ingestion.ingest --titles "Paris" "Tokyo"
    python -m ingestion.ingest --titles "Paris" "Tokyo" --dry-run
    python -m ingestion.ingest --titles "Paris" --concurrency 5

Fixes vs. the previous version:
- Bounded concurrency (asyncio.Semaphore) instead of unlimited asyncio.gather --
  at scale, unlimited concurrency means hundreds/thousands of simultaneous
  Wikivoyage requests and OpenAI calls at once, risking rate limits/blocks.
- Per-title error isolation -- one title failing (missing page, bad LLM
  response, etc.) no longer aborts the entire batch; failures are collected
  and reported, successful titles still get published.
- Idempotency skip -- if a title's content is unchanged since the last
  successful publish (raw_scrape.status is already "published" after
  fetch_title, since fetch.py preserves status when content_hash matches),
  skip re-parsing/re-enriching/re-embedding entirely. Saves OpenAI cost on
  repeat runs over an unchanged destination.
- Images now attached automatically after publish, via ingestion.images
  (extracts [[File:...]] references from the cached wikitext, resolves them
  through the Wikimedia Commons API).
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Any, List

from ingestion.embed import embed_raw_scrapes_batch
from ingestion.enrich import enrich_raw_scrape
from ingestion.fetch import fetch_title
from ingestion.images import attach_images_for_raw_scrape
from ingestion.parse import parse_raw_scrape
from ingestion.publish import publish_raw_scrape

DEFAULT_CONCURRENCY = 3  # keep this polite to Wikivoyage/OpenAI -- raise only
                          # once ingesting hundreds+ titles and you've confirmed
                          # neither API is rate-limiting you at this level.


async def process_title(title: str, semaphore: asyncio.Semaphore) -> dict[str, Any]:
    """Fetch, parse, and enrich one title. Never raises -- always returns a
    result dict describing the outcome, so one bad title can't take down the
    whole batch via asyncio.gather."""
    async with semaphore:
        try:
            raw = await fetch_title(title)
        except Exception as exc:
            return {"title": title, "status": "failed", "stage": "fetch", "error": str(exc)}

        if raw.status == "published":
            # fetch_title() only resets status to "fetched" when content_hash
            # changed; if it's still "published", this exact content was
            # already fully processed in a prior run.
            return {"title": title, "status": "skipped_unchanged", "raw_id": raw.id}

        try:
            raw = await parse_raw_scrape(raw.id)
        except Exception as exc:
            return {"title": title, "status": "failed", "stage": "parse", "error": str(exc)}

        try:
            raw = await enrich_raw_scrape(raw.id)
        except Exception as exc:
            return {"title": title, "status": "failed", "stage": "enrich", "error": str(exc)}

        return {"title": title, "status": "enriched", "raw_id": raw.id}


async def _main_async(args: argparse.Namespace) -> None:
    semaphore = asyncio.Semaphore(args.concurrency)
    results = await asyncio.gather(
        *(process_title(title, semaphore) for title in args.titles)
    )

    to_embed = [r for r in results if r["status"] == "enriched"]
    skipped = [r for r in results if r["status"] == "skipped_unchanged"]
    failed = [r for r in results if r["status"] == "failed"]

    print(
        f"\n-- fetch/parse/enrich complete: "
        f"{len(to_embed)} to embed, {len(skipped)} skipped (unchanged), {len(failed)} failed"
    )
    for r in failed:
        print(f"   FAILED [{r.get('stage', '?')}] {r['title']}: {r['error']}")

    published: list[Any] = []
    publish_failed: list[dict[str, Any]] = []

    if to_embed:
        raw_ids = [r["raw_id"] for r in to_embed]
        print(f"\n-- embedding {len(raw_ids)} destinations in one batch")
        embedded_raws = await embed_raw_scrapes_batch(raw_ids, dry_run=args.dry_run)
        print("-- embedding complete")

        for raw in embedded_raws:
            try:
                dest = await publish_raw_scrape(raw.id)
                print(f"  published: {dest.slug}")
                published.append(dest)

                if not args.skip_images:
                    try:
                        img_count = await attach_images_for_raw_scrape(raw.id, dest.id)
                        print(f"    images attached: {img_count}")
                    except Exception as exc:
                        # Image failures shouldn't undo an otherwise successful
                        # publish -- the destination is still usable without images.
                        print(f"    images FAILED (non-fatal): {exc}")
            except Exception as exc:
                publish_failed.append({"raw_id": raw.id, "error": str(exc)})
                print(f"  FAILED to publish raw_scrape {raw.id}: {exc}")

    print("\n== SUMMARY ==")
    print(f"  published:            {len(published)}")
    print(f"  skipped (unchanged):  {len(skipped)}")
    print(f"  failed (pre-publish): {len(failed)}")
    print(f"  failed (publish):     {len(publish_failed)}")
    if failed:
        print(f"  failed titles: {[r['title'] for r in failed]}")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the travel destination ingestion pipeline.")
    parser.add_argument("--titles", nargs="+", required=True, help="Wikivoyage titles to ingest.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Use zero-vector embeddings, no OpenAI embed cost."
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Max concurrent fetch/enrich operations (default {DEFAULT_CONCURRENCY}).",
    )
    parser.add_argument(
        "--skip-images", action="store_true", help="Skip fetching destination images."
    )
    args = parser.parse_args(argv)
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()