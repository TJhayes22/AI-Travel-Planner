# ADR-005: Hosting / Infrastructure

## Status
Accepted

## Context
Solo developer with a preference for traditional cloud (AWS) over fully serverless/managed
platforms, but with a hard constraint of not taking on more infrastructure operations burden
than one person can sustain.

## Decision
Use **AWS, but managed services only** — no self-managed servers or Kubernetes.

- **Backend**: AWS App Runner or ECS Fargate (containerized, no server/cluster management)
- **Frontend**: Vercel (purpose-built for Next.js) or S3 + CloudFront if staying fully on AWS
- **Database**: RDS for PostgreSQL (with pgvector support)
- **Object storage**: S3 (raw scraped data, images, uploads)
- **Queue**: SQS (see ADR-007)

## Alternatives Considered
- **Raw EC2 + self-managed Docker/Kubernetes**: Maximum control, but the operational burden
  (patching, scaling, orchestration, on-call) is not appropriate for a solo developer at this
  stage. Revisit only if a specific, well-understood scaling need arises that managed services
  can't meet.
- **Fully serverless-first vendor (e.g., Vercel + a BaaS)**: Faster initial setup, but less
  control and a less natural fit for a Python/FastAPI backend with background processing needs.

## Consequences
- Higher per-unit cost than raw compute, accepted as a trade for reduced operational time,
  which is the scarcer resource for a solo developer.
- Staying within managed AWS services keeps a path open to more control (e.g., moving to
  self-managed ECS/EKS) later without a full platform migration.
