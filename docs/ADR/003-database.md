# ADR-003: Database

## Status
Accepted

## Context
The platform needs standard relational data (users, listings, trips, reviews, categories) as
well as vector similarity search for matching user preference profiles to destination/listing
embeddings. The catalog is expected to grow from a small starting set to thousands of scraped
listings.

## Decision
Use **PostgreSQL with the pgvector extension**, hosted on RDS (see ADR-005).

- A single database serves both relational needs and vector similarity search, avoiding the
  operational overhead of running and syncing a separate vector database for a solo developer.
- pgvector performance is sufficient for a catalog in the thousands-to-tens-of-thousands range,
  which matches the stated growth target.
- Postgres full-text search (tsvector) also covers keyword search needs (see ADR-011), further
  reducing the number of separate systems required.

## Alternatives Considered
- **Postgres + a dedicated vector DB (Pinecone, Weaviate, etc.)**: Better vector search
  performance at very large scale, but adds a second system to operate, pay for, and keep in
  sync with the primary database. Not justified at the current or near-term scale.
- **MongoDB**: The data model here (users, listings, trips, categories, relationships between
  them) is genuinely relational; a document database would fight against that rather than help.

## Consequences
- If the catalog grows well beyond the thousands-to-tens-of-thousands range, pgvector's ANN
  search may become a bottleneck, and migrating to a dedicated vector database should be
  revisited at that point.
- All data lives in one system, simplifying backups, migrations, and local development for a
  solo developer.
