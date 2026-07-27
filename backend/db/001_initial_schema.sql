-- ============================================================================
-- Initial schema — Travel Recommendation Platform
-- Corresponds to ADR-003 (Database), ADR-004 (AI/Recommendation), ADR-009
-- (Data Ingestion Pipeline), ADR-010 (LLM Cost/Rate Control), ADR-014
-- (Booking Workflow).
--
-- Notes:
-- - Embedding dimension (1536) assumes an OpenAI-style embedding model.
--   Adjust to match whichever embedding model you actually use.
-- - This is written as plain DDL. In practice, run this through a migration
--   tool (e.g. Alembic) rather than applying it directly, so future schema
--   changes are tracked incrementally.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- fuzzy/keyword search support

-- ----------------------------------------------------------------------------
-- USERS
-- ----------------------------------------------------------------------------

CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_provider_id    TEXT NOT NULL UNIQUE, -- external id from Clerk/Auth0
    email               TEXT NOT NULL UNIQUE,
    display_name        TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Current derived preference profile — one row per user, overwritten as
-- preferences are updated (not a history log; see user_interactions for that).
CREATE TABLE user_preferences (
    user_id             UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    raw_input           TEXT,               -- latest free-text preferences from onboarding/quiz
    structured_tags     JSONB NOT NULL DEFAULT '{}', -- LLM-extracted structured preferences
    embedding           vector(1536),       -- generated from raw_input + structured_tags
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Note: user_interactions references destinations and listings, both defined
-- further down — it is created after them, near the end of this file.

-- ----------------------------------------------------------------------------
-- INGESTION (raw scrape staging — ADR-009)
-- ----------------------------------------------------------------------------

CREATE TABLE raw_scrapes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name         TEXT NOT NULL,          -- e.g. 'wikivoyage', 'manual'
    source_url          TEXT NOT NULL,
    s3_raw_key          TEXT NOT NULL,          -- pointer to raw HTML/JSON in S3
    content_hash        TEXT NOT NULL,          -- hash of raw content, drives re-enrichment skip (ADR-010)
    parsed_data         JSONB,                  -- output of the 'parse' stage
    status              TEXT NOT NULL DEFAULT 'fetched',
                        -- 'fetched' | 'parsed' | 'enriched' | 'published' | 'failed'
    error_message       TEXT,
    fetched_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_raw_scrapes_status ON raw_scrapes(status);
CREATE INDEX idx_raw_scrapes_content_hash ON raw_scrapes(content_hash);

-- ----------------------------------------------------------------------------
-- DESTINATIONS (published/live entities only)
-- ----------------------------------------------------------------------------

CREATE TABLE destinations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_scrape_id       UUID REFERENCES raw_scrapes(id) ON DELETE SET NULL,
    name                TEXT NOT NULL,
    slug                TEXT NOT NULL UNIQUE,
    country             TEXT,
    region              TEXT,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    description         TEXT,                  -- LLM-enriched summary
    cost_tier           SMALLINT,               -- e.g. 1 (budget) - 5 (luxury)
    climate             TEXT,
    best_season         TEXT,
    source_url          TEXT,
    status              TEXT NOT NULL DEFAULT 'draft',
                        -- 'draft' | 'enriched' | 'published' | 'archived'
    embedding           vector(1536),
    search_vector       tsvector,               -- keyword search (ADR-011)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_destinations_status ON destinations(status);
CREATE INDEX idx_destinations_search_vector ON destinations USING GIN(search_vector);
-- Vector similarity index — use hnsw if your pgvector version supports it,
-- ivfflat otherwise. Requires ANALYZE after bulk loads for ivfflat.
CREATE INDEX idx_destinations_embedding ON destinations
    USING hnsw (embedding vector_cosine_ops);

-- ----------------------------------------------------------------------------
-- TAGS (normalized taxonomy, LLM-assigned)
-- ----------------------------------------------------------------------------

CREATE TABLE tags (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL UNIQUE,
    category            TEXT NOT NULL -- 'vibe' | 'activity' | 'climate' | 'cost' | 'other'
);

CREATE TABLE destination_tags (
    destination_id      UUID NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    tag_id               INT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (destination_id, tag_id)
);

CREATE INDEX idx_destination_tags_tag_id ON destination_tags(tag_id);

-- ----------------------------------------------------------------------------
-- LISTINGS (stays — hotels, hostels, Airbnbs — attached to a destination)
-- ----------------------------------------------------------------------------

CREATE TABLE listings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    destination_id      UUID NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    listing_type        TEXT NOT NULL, -- 'hotel' | 'hostel' | 'airbnb' | 'resort' | 'other'
    price_tier          SMALLINT,
    rating              NUMERIC(2,1),
    booking_url         TEXT NOT NULL, -- referral/affiliate outbound link (ADR-014)
    affiliate_id        TEXT,
    source_name         TEXT,
    status              TEXT NOT NULL DEFAULT 'published',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_listings_destination_id ON listings(destination_id);

-- ----------------------------------------------------------------------------
-- USER INTERACTIONS (append-only log: views, saves, referral clicks, ratings)
-- Feeds (a) periodic recomputation of user_preferences.embedding, and
-- (b) recommendation-quality dashboards (ADR-013).
-- ----------------------------------------------------------------------------

CREATE TABLE user_interactions (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             UUID REFERENCES users(id) ON DELETE CASCADE,
    destination_id      UUID REFERENCES destinations(id) ON DELETE CASCADE,
    listing_id          UUID REFERENCES listings(id) ON DELETE SET NULL,
    interaction_type    TEXT NOT NULL, -- 'viewed' | 'saved' | 'searched' | 'booking_click' | 'rated'
    rating              SMALLINT,      -- optional, only for 'rated'
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX idx_user_interactions_destination_id ON user_interactions(destination_id);
CREATE INDEX idx_user_interactions_type ON user_interactions(interaction_type);

-- ----------------------------------------------------------------------------
-- ITINERARIES (LLM-generated, on-demand, cached — ADR-004 / ADR-010)
-- ----------------------------------------------------------------------------

CREATE TABLE itineraries (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    destination_id      UUID NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    cache_key           TEXT NOT NULL UNIQUE, -- hash of (user_id, destination_id, params)
    input_params        JSONB NOT NULL DEFAULT '{}', -- trip length, dates bucket, party size, etc.
    generated_content   JSONB NOT NULL,        -- the itinerary itself
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_itineraries_user_id ON itineraries(user_id);

-- ----------------------------------------------------------------------------
-- Trigger: keep destinations.search_vector in sync for keyword search
-- ----------------------------------------------------------------------------

CREATE FUNCTION destinations_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.region, '') || ' ' || coalesce(NEW.country, '')), 'C');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_destinations_search_vector
    BEFORE INSERT OR UPDATE ON destinations
    FOR EACH ROW EXECUTE FUNCTION destinations_search_vector_update();
