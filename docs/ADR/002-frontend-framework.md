# ADR-002: Frontend Framework

## Status
Accepted

## Context
The product is a discovery-oriented travel platform: destination and stay listing pages,
search, maps, and generated itineraries. Discoverability (SEO, shareable pages) matters for
a product whose core value is helping people find places. Solo developer, but should remain
approachable if a collaborator joins later.

## Decision
Use **Next.js (TypeScript)**.

- Server-side rendering / static generation support is valuable for destination and listing
  pages that should be indexable and shareable — a plain client-side SPA would hurt discovery,
  which is core to this product's value proposition.
- Large ecosystem and community — reduces solo-dev risk of getting stuck without support,
  and is easier to onboard a collaborator into later if the team grows.
- TypeScript adds type safety at the API boundary with the FastAPI backend.

## Alternatives Considered
- **Plain React SPA**: Simpler mental model, but no SSR/SSG out of the box, which is a real
  cost for a product whose growth depends partly on organic discovery of destination pages.
- **SvelteKit**: Comparable capabilities and often simpler, but smaller ecosystem — more risk
  for a solo developer who may need to solve tooling problems without much community support.

## Consequences
- Two languages to maintain (Python backend, TypeScript frontend) instead of one — accepted
  because frontend and backend concerns are different enough that this isn't a significant
  extra burden solo.
- Next.js has its own deployment quirks/conventions to learn if not already familiar.
