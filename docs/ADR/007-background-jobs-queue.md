# ADR-007: Background Jobs / Queue

## Status
Accepted

## Context
Several parts of the system are asynchronous batch or rate-controlled work rather than
request/response: ingesting and enriching scraped listings, generating embeddings, and
controlling the rate of LLM API calls during ingestion.

## Decision
Use **AWS SQS** with worker consumers (Fargate task or Lambda), rather than Celery + Redis.

- Since hosting is already on AWS (ADR-005), SQS avoids introducing and operating a separate
  stateful Redis instance purely for task queueing.
- SQS provides retry and dead-letter-queue support out of the box, useful for solo debugging
  when a scrape or enrichment step fails partway through a batch.

## Alternatives Considered
- **Celery + Redis**: More Python-native and flexible (e.g., complex task chaining, periodic
  tasks), but requires operating and monitoring an additional stateful service, which is extra
  solo-dev burden not clearly justified by current requirements.

## Consequences
- Slightly less flexible task orchestration than Celery for complex workflows; acceptable given
  the ingestion pipeline's stages (ADR-009) are straightforward and mostly linear.
- Keeps infrastructure surface area smaller, which matters more than task-orchestration
  flexibility at this stage.
