# ADR-014: Booking Workflow

## Status
Accepted

## Context
The product surfaces "booking-style workflows," but bookings are handled via referral/affiliate
handoff to external providers rather than in-app transactions — no payments are processed
directly by the platform.

## Decision
Implement booking as **referral/affiliate links with click tracking**, with no in-app
payment processing or inventory/availability management.

- Each listing stores an outbound URL, with an affiliate ID/tracking parameter where
  applicable (e.g., Booking.com, Expedia affiliate programs), added if/when such programs are
  joined.
- The "booking workflow" in-app is: user clicks "Book" → a click event is logged (for the
  analytics dashboards in ADR-013) → the user is redirected to the external provider's site.
- No new infrastructure is required for this; it uses the existing database (listing URLs) and
  PostHog (click tracking) already chosen.

## Alternatives Considered
- **In-app booking/payments**: Would require payment processing (e.g., Stripe), real-time
  availability/inventory sync with providers, and PCI-related considerations. Explicitly not
  needed given the referral-based model chosen.

## Consequences
- Significantly simpler and lower-risk than in-app transactions — no payment security surface,
  no inventory consistency requirements.
- Revenue (if any, via affiliate commissions) depends on external providers' affiliate program
  terms and tracking reliability, which is an external dependency rather than something the
  platform controls directly.
- If real-time price or availability checks become desirable later, that is additive
  (provider-specific API clients) rather than a redesign of this decision.
