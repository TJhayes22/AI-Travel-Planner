# ADR-015: Cost Tier Calculation

## Status
Proposed (not yet implemented — `destinations.cost_tier` is currently manually assigned
in `scripts/seed_destinations.py`, not calculated)

## Context
`destinations.cost_tier` (SMALLINT, 1-5) is used to give users a rough sense of how
expensive a destination is, displayed on the detail page as a `$`-`$$$$$` scale. Currently
this value is hardcoded per destination in the seed script, based on general judgment at
write-time — not derived from any real data. This doesn't scale to a growing, scraped
catalog (ADR-009), and isn't grounded in anything users can trust as accurate.

## Decision
**Primary approach: derive `cost_tier` from actual listing prices.**

Once a destination has associated `listings` with real `price_amount` values, calculate
`cost_tier` from the average or median nightly price across that destination's listings,
bucketed into 5 tiers (thresholds TBD based on real price distribution once listing data
exists — don't hardcode dollar-amount cutoffs speculatively here).

**Fallback: LLM-assigned during ingestion enrichment (see ADR-004, ADR-009).**

For destinations with no listings yet (or too few to be statistically meaningful), fall
back to the LLM enrichment step already planned for ingestion — the same pass that
extracts tags and generates the destination's embedding can also estimate a cost tier
from the scraped source content (e.g., a travel guide describing a destination as
"budget-friendly" or "upscale").

Destinations should track *which* method produced their current `cost_tier` (e.g. an
`cost_tier_source` column: `'listings'` | `'llm_estimate'` | `'manual'`), so the primary
method can be preferred over the fallback once real listing data accumulates, without
guessing which destinations still need recalculation.

## Alternatives Considered
- **Manual/curated only**: Fine for a small hand-picked catalog (current state), but
  explicitly doesn't scale to the thousands-of-listings goal from ADR-009 — a human
  can't eyeball cost tier for a scraped catalog at that size.
- **LLM-only (skip the listings-based approach entirely)**: Simpler (one method, not two),
  but less accurate than deriving from real prices once they exist — an LLM estimate from
  descriptive text is a proxy, actual listing prices are ground truth.

## Consequences
- Requires listing data to exist before the primary method is usable — until then, all
  destinations effectively rely on the fallback (or stay manually assigned, as now).
- Requires a decision (deferred to implementation time) on bucket thresholds once real
  price data exists to base them on.
- Adds one column (`cost_tier_source` or equivalent) to track provenance — small schema
  addition, not a redesign.
- This ADR should be revisited and moved to "Accepted" once implemented, likely alongside
  building out the ingestion pipeline (ADR-009) and/or once enough listings exist to make
  the primary method meaningful.