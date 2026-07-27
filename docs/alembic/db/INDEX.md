# Alembic Migrations — Complete Setup Index

## Overview

The Alembic migration system is now set up for your FastAPI + PostgreSQL backend. This document indexes all generated files and their purposes.

---

## Generated Files

### Core Migration Files

| File | Purpose | Status |
|------|---------|--------|
| [../../backend/alembic.ini](../../backend/alembic.ini) | Alembic configuration | Ready |
| [../../backend/alembic/env.py](../../backend/alembic/env.py) | Async SQLAlchemy environment setup | Ready |
| [../../backend/alembic/versions/0001_initial_schema.py](../../backend/alembic/versions/0001_initial_schema.py) | Initial schema (from 001_initial_schema.sql) | Ready |
| [../../backend/alembic/versions/0002_schema_hardening.py](../../backend/alembic/versions/0002_schema_hardening.py) | Schema hardening (from 002_schema_hardening.sql) | Ready |

### Documentation & Guides

| File | Purpose |
|------|---------|
| [README_SETUP.md](README_SETUP.md) | Complete setup instructions, environment config, running migrations |
| [VERIFICATION_GUIDE.md](VERIFICATION_GUIDE.md) | Exact commands to run + expected output for round-trip verification |
| [ASSUMPTIONS.md](ASSUMPTIONS.md) | All assumptions made, judgment calls, known limitations |
| **INDEX** (this file) | Overview and navigation |

### Infrastructure

| File | Purpose |
|------|---------|
| [../../backend/alembic/__init__.py](../../backend/alembic/__init__.py) | Alembic package marker |
| [../../backend/alembic/versions/__init__.py](../../backend/alembic/versions/__init__.py) | Versions package marker |
| [../../backend/app/db/__init__.py](../../backend/app/db/__init__.py) | Database module stub |
| [../../backend/app/db/base.py](../../backend/app/db/base.py) | SQLAlchemy declarative Base |

---

## Quick Start (30 seconds)

1. **Set environment variable:**
   ```bash
   export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/travel_planner"
   ```

2. **Move to backend directory:**
   ```bash
   cd backend/
   ```

3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Verify success:**
   ```bash
   alembic current  # Should print: 0002
   ```

---

## Full Round-Trip Verification

To verify the migrations work cleanly (up → down → up):

```bash
cd backend/

# Step 1: Upgrade to latest
alembic upgrade head

# Step 2: Check current revision
alembic current               # Expected: 0002

# Step 3: Downgrade to base
alembic downgrade base

# Step 4: Upgrade again
alembic upgrade head

# Step 5: Final check
alembic current               # Expected: 0002
```

For detailed output expectations, see [VERIFICATION_GUIDE.md](VERIFICATION_GUIDE.md).

---

## What Was Generated From Where

### Migration 0001: Initial Schema
- **Source:** `backend/db/001_initial_schema.sql`
- **Translates to Alembic:**
  - 3 extensions: `vector`, `pg_trgm`, `pgcrypto`
  - 9 tables: users, user_preferences, raw_scrapes, destinations, tags, destination_tags, listings, user_interactions, itineraries
  - 1 trigger function + trigger: `destinations_search_vector_update()`
  - ~15 indexes including HNSW vector similarity
  - Full-text search setup (tsvector)

### Migration 0002: Schema Hardening
- **Source:** `backend/db/002_schema_hardening.sql`
- **Translates to Alembic:**
  - 7 CHECK constraints for status/type validation
  - `set_updated_at()` trigger function + 5 per-table triggers
  - 4 new columns: embedding_model, embedding_updated_at, session_id, price attributes
  - 2 new tables: destination_images, listing_images
  - 2 unique partial indexes for primary image tracking

---

## When to Use Each Guide

- **[README_SETUP.md](README_SETUP.md)** — Setting up Alembic for the first time, running migrations, checking the schema
- **[VERIFICATION_GUIDE.md](VERIFICATION_GUIDE.md)** — Detailed command reference with exact expected output
- **[ASSUMPTIONS.md](ASSUMPTIONS.md)** — Understanding design decisions, known limitations, recommendations for future work
- **INDEX** (this file) — Quick navigation and overview

---

## Next Steps After Migrations

1. **Define ORM Models** — Create Python classes in `backend/app/models/` that inherit from `Base` in `backend/app/db/base.py`
2. **Generate Subsequent Migrations** — Once models are defined, use `alembic revision --autogenerate` for schema changes
3. **Add to CI/CD** — Include `alembic upgrade head` in your deployment pipeline
4. **Database Backups** — Set up automated backups before running migrations in production
5. **Version Control** — Ensure all alembic/ files are committed to git

For more, see [ASSUMPTIONS.md](ASSUMPTIONS.md#recommendations-for-going-forward).
