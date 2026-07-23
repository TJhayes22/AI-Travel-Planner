# ADR-010: LLM Cost & Rate Control

## Status
Accepted

## Context
Scraping and enriching thousands of listings implies thousands of LLM calls during ingestion
if done naively. Combined with on-demand itinerary generation, uncontrolled LLM usage is a
real cost and rate-limit risk — an explicit concern raised during planning.

## Decision
Control LLM usage via **queue-based processing and response caching**:

- Each listing to be enriched is pushed through the SQS queue (ADR-007) rather than calling
  the LLM API for the whole batch at once. A worker processes the queue at a controlled rate,
  respecting the provider's rate limits and smoothing cost spikes.
- LLM enrichment output is **cached, keyed by a hash of the input content**. If a listing is
  re-scraped and its content hasn't meaningfully changed, the cached enrichment is reused
  instead of triggering a new LLM call.
- Itinerary generation (on-demand, per ADR-004) is similarly cached by
  (user, destination, date-range-bucket) to avoid repeat calls for near-identical requests.

## Alternatives Considered
- **No queueing, direct batch calls**: Simplest to implement, but risks hitting provider rate
  limits and produces unpredictable cost spikes during large ingestion runs — directly
  conflicts with the stated cost concern.

## Consequences
- Ingestion of a large batch of new listings takes longer wall-clock time (queued/rate-limited)
  rather than completing as fast as the API allows — an acceptable trade for cost predictability
  and reliability.
- Requires a content-hashing/caching layer to be built as part of the ingestion pipeline rather
  than added later.
