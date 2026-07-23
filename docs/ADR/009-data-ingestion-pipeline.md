# ADR-009: Data Ingestion / Scraping Pipeline

## Status
Accepted

## Context
The listing catalog will grow from a small starting set to thousands of scraped
destinations/stays, per an explicit maintainability principle: the ingestion approach must
handle that growth without requiring a rewrite. Scraping thousands of listings is a batch
process, not a request/response operation, and needs to be independently debuggable when a
given source or stage fails.

## Decision
Build a **standalone, scheduled ingestion service**, decoupled from the main API, structured
as a staged pipeline with each stage independently re-runnable:

1. **Fetch** — scrape raw listing data, store raw HTML/JSON in S3 (source of truth, allows
   reprocessing without re-scraping).
2. **Parse** — extract structured fields into a staging table in Postgres.
3. **Enrich** — LLM categorization pass (tags, summary) — see ADR-004.
4. **Embed** — generate and store the listing's vector embedding in pgvector.
5. **Publish** — mark the listing "live" in the main listings table, separating
   in-process/failed records from what's visible to users.

Triggered on a schedule (e.g., EventBridge → Fargate task, or a scheduled Lambda for smaller
per-run volumes).

## Alternatives Considered
- **Inline scrape-and-process script**: Faster to build initially, but given the explicit goal
  of growing to thousands of listings with a maintainability principle in mind, this would need
  to be rewritten within months. Building the staged pipeline now is the more cost-effective
  path given the stated requirements.

## Consequences
- More upfront pieces to build (five stages vs. one script), but each is small, testable, and
  independently debuggable — important for a solo developer diagnosing a failed scrape or bad
  batch without unwinding a monolithic process.
- Raw data retained in S3 means reprocessing (e.g., after an enrichment prompt change) doesn't
  require re-scraping sources, which is valuable both for cost and for respecting scraped
  sources' load.
