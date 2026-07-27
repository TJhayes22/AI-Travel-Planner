# AI Travel Planner

An AI-powered travel recommendation platform that leverages personalized preferences, vector embeddings, and large language models to generate tailored destination recommendations and itineraries.

## Overview

AI Travel Planner helps users discover destinations and accommodations through intelligent semantic search and personalized recommendations. The system combines real-time preference-based matching with on-demand LLM-generated itineraries, enabling travelers to explore curated suggestions tailored to their interests and travel history.

## Features

- **Semantic Search and Ranking** — pgvector-powered similarity search matches user preferences against destination embeddings
- **Personalized Recommendations** — User profiles capture preferences and travel history for contextualized suggestions
- **LLM-Generated Itineraries** — On-demand creation of detailed trip plans with activity suggestions and logistics
- **Booking Integration** — Referral-based links to external providers with click tracking and analytics
- **Real-time Analytics** — PostHog for engagement metrics and Metabase for recommendation quality dashboards
- **Scalable Ingestion Pipeline** — Staged, fault-tolerant data pipeline for scraping and enriching listing catalogs

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (TypeScript, SSR/SSG)
- **Database**: PostgreSQL with pgvector extension
- **Search**: PostgreSQL full-text search (tsvector) and pgvector
- **Hosting**: AWS (App Runner/ECS Fargate, RDS, S3, CloudFront)
- **Queue**: AWS SQS with Fargate workers
- **Auth**: Clerk or Auth0
- **Analytics**: PostHog, Metabase
- **Maps**: Mapbox
- **Error Tracking**: Sentry
- **Monitoring**: CloudWatch
- **CI/CD**: GitHub Actions

For detailed architectural decisions, see [ADR Documentation](docs/ADR/).

## Project Structure

```
├── backend/           # FastAPI application and ingestion pipeline
│   ├── app/          # Main API and services
│   ├── alembic/      # Database migrations (Alembic)
│   ├── ingestion/    # Data scraping and enrichment pipeline
│   ├── llm/          # LLM integration and prompts
│   ├── tests/        # Test suite
│   └── db/           # Raw SQL schemas (reference)
├── frontend/         # Next.js application
│   ├── app/          # Pages and routes
│   ├── components/   # Reusable React components
│   └── lib/          # Utilities and API clients
├── infrastructure/   # AWS and Docker configurations
├── docs/             # Documentation and ADRs
│   ├── ADR/          # Architecture Decision Records
│   └── alembic/db/   # Database migration guides
└── scripts/          # Utility scripts
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- AWS account (for deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd AI-Travel-Planner
   ```

2. **Backend setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Database setup**
   ```bash
   createdb travel_planner
   psql travel_planner -c "CREATE EXTENSION IF NOT EXISTS vector"
   psql travel_planner -c "CREATE EXTENSION IF NOT EXISTS pg_trgm"
   psql travel_planner -c "CREATE EXTENSION IF NOT EXISTS pgcrypto"
   cd backend && alembic upgrade head
   ```

5. **Environment configuration**
   - Copy `.env.example` to `.env` in both backend and frontend directories
   - Configure API keys (Clerk/Auth0, LLM provider, Mapbox, etc.)
   - Set `DATABASE_URL` environment variable for Alembic migrations

6. **Run locally**
   - Backend: `cd backend && uvicorn app.main:app --reload`
   - Frontend: `cd frontend && npm run dev`

See [Database Migrations](docs/alembic/db/README_SETUP.md) for detailed Alembic setup and [Development Setup](docs/setup.md) for other instructions.

## Deployment

Deployment follows AWS managed services patterns. See [Deployment Guide](docs/deployment.md) for infrastructure setup, environment configuration, and CI/CD workflows.

## Architecture

The system is organized into three primary components:

1. **API Layer** (FastAPI) — Serves search, recommendations, and itinerary generation endpoints
2. **Ingestion Pipeline** — Staged batch processing for scraping, parsing, enriching, embedding, and publishing listings
3. **Frontend** (Next.js) — Server-rendered pages for discoverability, interactive search, and itinerary browsing

Data flows from scraped sources through the ingestion pipeline (fetch → parse → enrich → embed → publish) into PostgreSQL, where both the API and analytics queries operate.

For a detailed system architecture diagram and component interactions, see [Architecture Documentation](docs/architecture.md).

## Contributing

Contributions are welcome. Please see [Contributing Guidelines](docs/CONTRIBUTING.md) for development workflows and code standards.

## Monitoring and Troubleshooting

- Application errors: Sentry dashboard
- Infrastructure metrics: CloudWatch
- Product analytics: PostHog
- Recommendation quality: Metabase dashboards
- Logs: CloudWatch Logs

See [Troubleshooting Guide](docs/troubleshooting.md) for common issues.

## License

See [LICENSE](LICENSE) file for details.