#!/bin/bash
# Quick reference: Alembic migration verification commands
# Run from backend/ directory

set -e

echo "=========================================="
echo "Alembic Migration Verification"
echo "=========================================="
echo ""

# Ensure DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable not set"
    echo "Set it with: export DATABASE_URL=\"postgresql+asyncpg://user:pwd@host/dbname\""
    exit 1
fi

echo "Using DATABASE_URL: $DATABASE_URL"
echo ""

# STEP 1: Upgrade to head
echo "STEP 1: Running 'alembic upgrade head'..."
alembic upgrade head
echo "✓ Upgrade complete"
echo ""

# STEP 2: Check current revision
echo "STEP 2: Running 'alembic current'..."
CURRENT=$(alembic current)
echo "Current revision: $CURRENT"
if [ "$CURRENT" = "0002" ]; then
    echo "✓ Correct revision (0002)"
else
    echo "✗ Unexpected revision: $CURRENT (expected 0002)"
    exit 1
fi
echo ""

# STEP 3: Downgrade to base
echo "STEP 3: Running 'alembic downgrade base'..."
alembic downgrade base
echo "✓ Downgrade complete"
echo ""

# STEP 4: Verify base state
echo "STEP 4: Verifying base state (alembic current)..."
CURRENT=$(alembic current)
if [ -z "$CURRENT" ] || [ "$CURRENT" = "<empty>" ]; then
    echo "✓ Database is at base (no migrations applied)"
else
    echo "✗ Database not at base. Current: $CURRENT"
    exit 1
fi
echo ""

# STEP 5: Upgrade again
echo "STEP 5: Running 'alembic upgrade head' again..."
alembic upgrade head
echo "✓ Second upgrade complete"
echo ""

# STEP 6: Final verification
echo "STEP 6: Final check (alembic current)..."
CURRENT=$(alembic current)
echo "Current revision: $CURRENT"
if [ "$CURRENT" = "0002" ]; then
    echo "✓ Round-trip successful!"
else
    echo "✗ Unexpected revision: $CURRENT"
    exit 1
fi
echo ""

echo "=========================================="
echo "✓ ALL CHECKS PASSED"
echo "=========================================="
echo ""
echo "Your schema is now fully migrated and ready for use."
echo "To verify tables and indexes in PostgreSQL, run:"
echo ""
echo "  psql -d travel_planner -c '\\dt'      # List tables"
echo "  psql -d travel_planner -c '\\di'      # List indexes"
echo "  psql -d travel_planner -c '\\d destinations'  # Show table structure"
echo ""
