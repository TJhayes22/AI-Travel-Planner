# ADR-013: Analytics / Dashboards

## Status
Accepted

## Context
The product needs to monitor both general user engagement (clicks, searches, conversions) and
recommendation quality specifically (e.g., click-through rate on suggested destinations,
itinerary acceptance rate), to support the "supports scalable search and personalization"
goal over time.

## Decision
Use **PostHog** for engagement event tracking, and **Metabase** on top of PostgreSQL for
recommendation-quality dashboards.

- PostHog covers general product analytics (clicks, searches, conversions, referral-link
  clicks) with minimal setup, with a usable free/cloud tier.
- Recommendation-quality metrics are fundamentally queries over the platform's own event data
  already stored in Postgres; Metabase provides dashboards over that data without building a
  custom internal admin/analytics UI.

## Alternatives Considered
- **Custom-built analytics/admin UI**: Full control, but a significant build cost for
  functionality that off-the-shelf tools already provide well.
- **A single unified analytics platform for both use cases**: Would simplify tooling, but no
  single tool evaluated covered both general product analytics and ad-hoc SQL-based dashboards
  over custom recommendation-quality metrics as well as this two-tool combination.

## Consequences
- Two separate tools to maintain rather than one, though both are low-maintenance, managed
  services rather than self-hosted infrastructure to operate.
