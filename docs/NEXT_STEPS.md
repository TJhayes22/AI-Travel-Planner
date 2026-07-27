# Next Steps for AI-Travel-Planner Development

**Current Date:** July 26, 2026  
**Session Summary:** Completed Alembic migration setup with full round-trip verification ✅

---

## Session Recap

✅ **Completed:**
- Translated raw SQL schemas (001_initial_schema.sql, 002_schema_hardening.sql) into Alembic migrations
- Set up async SQLAlchemy + PostgreSQL integration (switched to sync for migrations due to async complexity)
- Fixed all type errors (TIMESTAMPTZ → postgresql.TIMESTAMP) and import issues (pgvector.Vector)
- Verified database connectivity and credentials
- Achieved full round-trip migration success: upgrade → downgrade → upgrade all passing
- Cleaned up repository: moved Alembic docs to docs/alembic/db/, removed redundant migrations/ folder
- Updated root README with database setup and migration references

**Current State:**
- Database schema fully applied and verified
- `alembic current` returns: `0002` (head)
- All 11 tables created with proper indexes, triggers, and constraints
- All 3 PostgreSQL extensions installed (vector, pg_trgm, pgcrypto)
- Ready for backend application development

---

## Immediate Next Session (1-2 hours)

### Priority 1: Define ORM Models (High Impact)
**Why:** Your FastAPI application needs SQLAlchemy models to interact with the database  
**What:** Create Python ORM classes for each table (users, destinations, listings, etc.)  
**Where:** `backend/app/models/`  
**Tasks:**
1. Create `backend/app/models/__init__.py` (export all models)
2. Create base model class inheritance from `backend/app/db/base.Base`
3. Define 11 model classes:
   - users.py
   - user_preferences.py
   - raw_scrapes.py
   - destinations.py
   - tags.py
   - destination_tags.py
   - listings.py
   - user_interactions.py
   - itineraries.py
   - destination_images.py (new in 0002)
   - listing_images.py (new in 0002)

**Reference:** Use alembic migration files as schema source of truth for column names, types, constraints

**Dependencies:**
- sqlalchemy>=2.0
- sqlalchemy[asyncio] if using async ORM queries

**Expected Outcome:** Full ORM model definitions with relationships, validators, and type hints

---

### Priority 2: Create FastAPI Schemas (High Impact)
**Why:** Schemas define API request/response contracts  
**What:** Pydantic v2 models for serialization/validation  
**Where:** `backend/app/schemas/`  
**Tasks:**
1. Create base schemas (BaseXXX) with common fields
2. Create CRUD schemas (XXXCreate, XXXUpdate, XXXRead) for each table
3. Include relationships (e.g., User → [UserPreferences])
4. Use discriminated unions for polymorphic types (if needed)
5. Add field validators for enums (status, type fields)

**Reference:** Check ADRs for validation rules, especially:
- ADR-003 (Database schema)
- ADR-004 (AI recommendation approach) for embedding-related fields

**Expected Outcome:** Complete request/response contract definitions

---

### Priority 3: Set Up Database Session & Dependency Injection (Medium Priority)
**Why:** FastAPI needs a way to inject database sessions into route handlers  
**What:** Create async session factory and FastAPI dependency  
**Where:** `backend/app/core/database.py`  
**Tasks:**
1. Create async session factory using SQLAlchemy's SessionLocal
2. Implement FastAPI dependency for session injection
3. Handle transaction lifecycle (begin, commit, rollback)
4. Add connection pooling configuration

**Reference:** See `backend/alembic/env.py` for current SQLAlchemy configuration

**Expected Outcome:** Routes can inject sessions: `async def get_users(db: Session = Depends(get_db))`

---

## Medium-Term Next Steps (Next 1-2 Sessions)

### 4. Implement Core API Routes (3-5 hours)
- Start with read-only endpoints (GET)
- Build out CRUD operations for primary entities:
  - Users (GET, POST, PATCH)
  - Destinations (GET, search, recommendations)
  - Listings (GET, filter)
  - User interactions (POST for logging)

### 5. Set Up Authentication & Authorization (2-3 hours)
- Integrate Clerk or Auth0 (per ADR-006)
- Create middleware for token validation
- Implement per-route permission checks
- Set up user context middleware

### 6. Implement Vector Search (2-3 hours)
- Create pgvector similarity search queries
- Integrate into destination search/recommendations
- Set up embedding generation pipeline
- (Requires LLM client setup first)

### 7. Configure LLM Integration (1-2 hours)
- Set up LLM client (OpenAI, Anthropic, etc.)
- Create prompt templates in `backend/llm/prompts/`
- Implement itinerary generation endpoint
- Add cost/rate limiting (per ADR-010)

### 8. Set Up Background Job Queue (1-2 hours)
- Configure AWS SQS workers (per ADR-007)
- Implement data ingestion pipeline (per ADR-009)
- Create Celery/Prefect task definitions

---

## Before Next Session: Prep Work (Optional, ~15 min)

- [ ] Review [docs/alembic/db/](docs/alembic/db/) — particularly ASSUMPTIONS.md for schema details
- [ ] Read ADR-003 (Database) and ADR-004 (AI Approach) for business logic context
- [ ] Check `backend/db/001_initial_schema.sql` and `002_schema_hardening.sql` for exact column specs
- [ ] Decide on async vs sync SQLAlchemy approach (current setup supports both)
- [ ] Verify PostgreSQL 15+ is still running: `psql --version`

---

## Decision Points for Next Session

### Async vs Sync ORM Queries?
- **Current:** Migrations use async engine (asyncpg driver)
- **Options:**
  - A) Keep async (FastAPI native, better concurrency) — requires async session management
  - B) Switch to sync (simpler, works with current env.py) — less optimal for I/O-heavy app
- **Recommendation:** Option A (async) — aligns with FastAPI best practices

### Authentication Strategy?
- **Current:** ADR-006 mentions Clerk or Auth0
- **Decision needed:** Which service? How to handle user creation sync?

### Vector Embedding Source?
- **Current:** Tables have columns for embeddings but no generation logic
- **Decision needed:** When/where to generate? During ingestion? On-demand? Pre-populated?

---

## Reference Materials Already in Place

- [docs/alembic/db/README_SETUP.md](docs/alembic/db/README_SETUP.md) — Migration commands & verification
- [docs/alembic/db/VERIFICATION_GUIDE.md](docs/alembic/db/VERIFICATION_GUIDE.md) — Exact command reference
- [docs/alembic/db/ASSUMPTIONS.md](docs/alembic/db/ASSUMPTIONS.md) — Implementation decisions & limitations
- [docs/ADR/](docs/ADR/) — Architecture Decision Records (especially 003, 004, 006, 007, 009, 010)
- [backend/db/](backend/db/) — Original SQL schemas (source of truth)

---

## Files & Folders to Create Next

```
backend/
├── app/
│   ├── models/               ← CREATE (Task 1)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── destination.py
│   │   ├── listing.py
│   │   ├── ... (etc)
│   ├── schemas/              ← CREATE (Task 2)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── destination.py
│   │   ├── ... (etc)
│   └── core/
│       ├── database.py       ← MODIFY (Task 3)
│       ├── config.py         ← MODIFY (add session config)
```

---

## Success Criteria for Next Session

By the end of your next session, you should be able to:

1. ✅ Run: `cd backend && python -c "from app.models import User; print(User.__tablename__)"`
2. ✅ Run: `cd backend && python -c "from app.schemas import UserCreate; u = UserCreate(email='test@example.com', name='Test')"` (validation passes)
3. ✅ Run: `cd backend && alembic current` (still returns 0002)
4. ✅ Start FastAPI: `cd backend && uvicorn app.main:app --reload` (server starts without import errors)

---

## Blocking Issues to Resolve First

None! All Alembic setup is complete. You're ready to start backend development.

---

## Questions to Ask Before Starting

- Should models be async-only, or support both async/sync queries?
- Do you want to use SQLModel (Pydantic + SQLAlchemy hybrid) or keep them separate?
- Which LLM provider for embeddings? (affects prompt management)
- Is the user creation flow manual or automatic on first login (Clerk/Auth0)?

---

**Session Completed:** July 26, 2026  
**Next Recommended Session:** ASAP (models are blocking many other tasks)  
**Estimated Time for Next Session:** 2-3 hours for models + schemas + session setup
