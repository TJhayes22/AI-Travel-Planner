# ADR-001: Backend Framework

## Status
Accepted

## Context
Solo developer, Python preferred (strong fit for AI/ML integration work). The backend needs
to serve a JSON API to a Next.js frontend, handle I/O-bound work (LLM API calls, database
queries, external map/booking links), and stay maintainable by one person as the listing
catalog grows into the thousands.

## Decision
Use **FastAPI**.

- Async-native, which matters heavily here since most backend work is I/O-bound (LLM API
  calls, DB queries, external requests) rather than CPU-bound.
- Pydantic-based request/response validation pairs naturally with structured LLM outputs
  (e.g., validating that an LLM's JSON categorization response matches an expected schema).
- Auto-generated OpenAPI docs, useful for a solo dev who won't have a separate API-docs writer.

## Alternatives Considered
- **Django**: Excellent batteries-included admin panel and ORM, but sync-first by default and
  heavier than needed for an API-only backend. Its strengths (admin UI, auth system) are less
  valuable here since auth is being handled by a dedicated provider (ADR-006).
- **Flask**: Simple and familiar, but async support and request validation would need to be
  hand-assembled from extensions rather than built in.

## Consequences
- Smaller "batteries included" ecosystem than Django — a separate admin panel (e.g. SQLAdmin)
  will be needed if internal data-management tooling is required later.
- Async patterns need to be used consistently (e.g., async DB drivers) to get the full benefit;
  mixing sync and async carelessly can silently reintroduce blocking calls.
