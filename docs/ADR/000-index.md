# Architecture Decision Records — Travel Recommendation Platform

This folder contains the ADRs for the initial architecture of the AI-powered travel
recommendation platform (search, personalized recommendations, itinerary generation,
referral-based booking).

| ADR | Title | Status |
|---|---|---|
| [001](001-backend-framework.md) | Backend Framework | Accepted |
| [002](002-frontend-framework.md) | Frontend Framework | Accepted |
| [003](003-database.md) | Database | Accepted |
| [004](004-ai-recommendation-approach.md) | AI / Recommendation Approach | Accepted |
| [005](005-hosting-infra.md) | Hosting / Infrastructure | Accepted |
| [006](006-auth.md) | Authentication | Accepted |
| [007](007-background-jobs-queue.md) | Background Jobs / Queue | Accepted |
| [008](008-cicd-monitoring.md) | CI/CD & Monitoring | Accepted |
| [009](009-data-ingestion-pipeline.md) | Data Ingestion / Scraping Pipeline | Accepted |
| [010](010-llm-cost-rate-control.md) | LLM Cost & Rate Control | Accepted |
| [011](011-search-engine.md) | Search Engine | Accepted |
| [012](012-maps.md) | Maps | Accepted |
| [013](013-analytics-dashboards.md) | Analytics / Dashboards | Accepted |
| [014](014-booking-workflow.md) | Booking Workflow | Accepted |

## Context for all ADRs

- **Team**: Solo dev (Tyler Hayess)
- **Backend language preference**: Python
- **Hosting preference**: Traditional cloud (AWS), managed services to minimize solo ops burden
- **Scale target**: Start small, designed to grow to thousands of scraped destination/stay listings
- **Product flow**: Users search destinations/stays → recommendation engine ranks listings by
  preferences and history → LLM generates personalized suggestions and itineraries on demand →
  frontend displays listings, maps, and trip plans → referral-style outbound links handle
  booking → dashboards monitor engagement and recommendation quality.
