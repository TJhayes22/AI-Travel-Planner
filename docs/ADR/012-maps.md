# ADR-012: Maps

## Status
Accepted

## Context
The frontend needs to display listings and destinations on a map as part of the browsing and
trip-planning experience.

## Decision
Use **Mapbox**.

- Lower cost at scale compared to Google Maps.
- Generous free tier appropriate for a pre-revenue solo project.
- Good React/Next.js SDK support and highly customizable map styling, useful for giving the
  product a distinct visual identity rather than a generic map look.

## Alternatives Considered
- **Google Maps Platform**: Stronger raw point-of-interest data, which could matter if POI
  richness becomes a differentiator later, but pricing is less favorable at scale.

## Consequences
- Mapbox is the default choice now; if POI data quality becomes a limiting factor later, this
  should be revisited, since the two providers are reasonably swappable at the integration
  layer.
