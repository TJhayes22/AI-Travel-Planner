# ADR-008: CI/CD & Monitoring

## Status
Accepted

## Context
Solo developer needs low-maintenance, low-cost tooling for deployment automation, error
tracking, and infrastructure monitoring, without spending significant setup or ongoing
maintenance time.

## Decision
Use **GitHub Actions** for CI/CD, **Sentry** for application error tracking, and
**CloudWatch** for AWS infrastructure metrics.

- All three have generous free tiers appropriate for a pre-revenue solo project.
- GitHub Actions integrates directly with the source repository with minimal setup.
- Sentry surfaces application-level errors (backend and frontend) in one place, which matters
  for a solo developer without a team to notice issues informally.
- CloudWatch is already included with the AWS services chosen in ADR-005, avoiding a separate
  infra-monitoring tool.

## Alternatives Considered
- **Self-hosted CI (e.g., Jenkins)**: Unnecessary operational overhead for a solo project.
- **Datadog or similar full observability suite**: More powerful, but costs scale quickly and
  overlaps significantly with what CloudWatch + Sentry already cover at this stage.

## Consequences
- Monitoring is split across two tools (Sentry for errors, CloudWatch for infra) rather than
  one unified dashboard — acceptable trade for cost, revisit if/when a single-pane-of-glass
  tool becomes worth the expense.
