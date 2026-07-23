# ADR-006: Authentication

## Status
Accepted

## Context
User accounts are needed to store preferences, trip history, and personalization data. Solo
developer, minimal appetite for maintaining custom auth or debugging complex identity
provider integrations.

## Decision
Use a **managed auth provider — Clerk or Auth0** (final choice between the two deferred to
implementation time, based on pricing/DX at that point) rather than AWS Cognito or a
hand-rolled auth system.

- Both integrate with a Python backend via standard JWT verification, and provide
  ready-made frontend components for Next.js.
- Substantially better developer experience than Cognito, which is known to be difficult and
  time-consuming to integrate correctly, a poor trade for a solo developer's time.

## Alternatives Considered
- **AWS Cognito**: Cheaper at scale and stays within the AWS ecosystem, but has a reputation
  for painful integration and configuration overhead that isn't worth the savings pre-revenue.
- **Custom auth (e.g., hand-rolled sessions/JWT)**: Full control, but auth bugs are a
  particularly costly place to make mistakes, and this is undifferentiated work for the product.

## Consequences
- Recurring cost that scales with monthly active users — acceptable given the time saved.
- Vendor dependency for a critical piece of the system; both Clerk and Auth0 support standard
  JWT-based verification, keeping backend integration relatively provider-agnostic if a
  migration is ever needed.
