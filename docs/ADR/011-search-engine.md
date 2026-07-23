# ADR-011: Search Engine

## Status
Accepted

## Context
Users search for destinations and stays, which needs to support both keyword search and
preference-based semantic matching. Catalog size target is thousands of listings, not
hundreds of thousands.

## Decision
Use **PostgreSQL full-text search (tsvector) combined with pgvector**, without introducing a
separate dedicated search engine.

- At a catalog size of thousands, this combination covers both keyword search and
  semantic/preference-based search without adding another system to operate.
- Reuses the same database already chosen for relational and vector data (ADR-003), keeping
  operational surface area minimal for a solo developer.

## Alternatives Considered
- **Elasticsearch / OpenSearch**: Powerful, but a substantial operational burden (cluster
  management, indexing pipeline) that isn't justified at thousands-of-listings scale.
- **Typesense / Meilisearch**: Lighter-weight than Elasticsearch and much easier to run solo;
  a reasonable next step if faceted search complexity or scale outgrows Postgres, but not
  needed at current scope.

## Consequences
- Revisit this decision if the catalog grows past roughly 100k+ listings, or if search needs
  evolve toward complex multi-facet filtering (price/date/amenity combinations) that starts to
  strain Postgres's query planner.
