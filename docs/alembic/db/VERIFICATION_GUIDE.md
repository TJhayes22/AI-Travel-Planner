# Exact Verification Commands & Expected Output

This document shows the exact commands to run to verify the Alembic migrations work end-to-end.

---

## Pre-Flight Checklist

Before running any commands, ensure:

1. **PostgreSQL 15+ is running** and accessible
2. **DATABASE_URL is set** in your shell:
   ```bash
   # Linux/macOS
   export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/travel_planner"
   
   # Windows PowerShell
   $env:DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/travel_planner"
   ```

3. **Python dependencies are installed**:
   ```bash
   pip install sqlalchemy[asyncio] asyncpg alembic pgvector psycopg2-binary
   ```

4. **Working directory is `backend/`**:
   ```bash
   cd /path/to/AI-Travel-Planner/backend
   ```

---

## Command 1: Upgrade to Latest Schema

**Command:**
```bash
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial_schema
INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002, schema_hardening
```

**What it does:**
- Creates all 9 tables
- Installs 3 extensions (vector, pg_trgm, pgcrypto)
- Creates triggers and indexes
- Adds CHECK constraints

---

## Command 2: Check Current Revision

**Command:**
```bash
alembic current
```

**Expected Output:**
```
0002
```

**Interpretation:**
- Database is at revision 0002 (latest)
- Both migrations have been applied successfully

---

## Command 3: Downgrade to Base (Empty Schema)

**Command:**
```bash
alembic downgrade base
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running downgrade 0002 -> 0001, schema_hardening
INFO  [alembic.runtime.migration] Running downgrade 0001 -> , initial_schema
```

**What it does:**
- Drops image tables
- Removes all the hardening columns/constraints
- Drops initial tables
- Removes extensions

**Verify the downgrade worked:**
```bash
alembic current
```

Expected output: (nothing, or `<empty>`)

---

## Command 4: Upgrade Again (Round-Trip Verification)

**Command:**
```bash
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial_schema
INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002, schema_hardening
```

**What it does:**
- Re-applies all migrations from scratch
- Should complete without errors

**Verify final state:**
```bash
alembic current
```

Expected output:
```
0002
```

---

## Full Round-Trip Script (All 4 Steps)

Copy this entire block and run at once:

```bash
#!/bin/bash
cd backend/
echo "Step 1: Upgrade to latest"
alembic upgrade head
echo ""
echo "Step 2: Check current revision"
alembic current
echo ""
echo "Step 3: Downgrade to base"
alembic downgrade base
echo ""
echo "Step 4: Upgrade again"
alembic upgrade head
echo ""
echo "Final check:"
alembic current
echo ""
echo "✓ Round-trip complete!"
```

---

## Optional: Inspect the Schema in PostgreSQL

After running `alembic upgrade head`, verify the schema was created:

```bash
# Connect to the database
psql -U user -d travel_planner

# Inside psql:

-- List all tables
\dt

-- Expected output (9 tables from 0001 + 2 from 0002):
--   public | destination_images      | table
--   public | destination_tags        | table
--   public | destinations            | table
--   public | itineraries             | table
--   public | listing_images          | table
--   public | listings                | table
--   public | raw_scrapes             | table
--   public | tags                    | table
--   public | user_interactions       | table
--   public | user_preferences        | table
--   public | users                   | table

-- List extensions
SELECT * FROM pg_extension;

-- Expected: vector, pg_trgm, pgcrypto, plpgsql

-- Verify a table structure
\d destinations

-- Expected columns (partial):
--   id                    | uuid
--   name                  | text
--   embedding             | vector(1536)  [pgvector]
--   search_vector         | tsvector
