# ADR-004: AI / Recommendation Approach

## Status
Accepted

## Context
The product needs to: (1) categorize destinations/listings and user preferences, (2) rank
listings for a given user's search based on preferences and history, and (3) generate
personalized itineraries and travel suggestions on demand. The catalog will grow into the
thousands via scraping, so the approach must keep LLM usage (and cost) roughly flat regardless
of catalog size, and must not add LLM latency to every search request.

## Decision
Use a **hybrid approach**: LLM enrichment at ingestion time, embeddings + vector search for
real-time ranking, and LLM generation only for on-demand itinerary/suggestion output.

Specifically:
1. **Ingestion (once per listing)**: An LLM extracts structured tags/attributes from scraped
   listing data (vibe, activities, cost tier, climate, etc.). An embedding is generated from
   this structured summary and stored in pgvector.
2. **User profiling (on profile creation/update)**: The same tag/embedding process runs on
   user preferences (onboarding answers, free-text input, trip history).
3. **Search / ranking (every search)**: Pure vector similarity search + filters against
   pgvector — **no LLM call on the search path**.
4. **Itinerary / suggestion generation (on demand, user-triggered)**: An LLM call generates
   the personalized itinerary or explanation, triggered only when a user explicitly requests
   a trip plan. Cacheable by (user, destination, date-range-bucket).

## Alternatives Considered
- **Pure LLM recommendation** (LLM ranks/selects from full listing context at query time):
  Fastest to prototype, but does not scale — LLM cost and latency would grow with catalog size
  and search volume, which conflicts directly with the stated growth target and cost concerns.
- **Pure statistical/collaborative-filtering recommender with no LLM**: Would avoid LLM costs
  entirely, but loses the ability to handle free-text preferences and generate personalized
  narrative itineraries, which are core to the product's value proposition.

## Consequences
- LLM calls scale with *catalog size and profile updates*, not with *search or browsing
  volume* — this is the key cost control and directly addresses the "don't want that many
  calls" constraint.
- Requires building the ingestion pipeline (ADR-009) and queueing/rate control (ADR-010) up
  front rather than deferring them, since the embeddings-based approach depends on them from
  day one.
- Itinerary generation should be cached and possibly rate-limited per user to control cost
  from adversarial/repeated use.
