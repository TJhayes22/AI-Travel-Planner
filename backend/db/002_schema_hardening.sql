-- ============================================================================
-- Migration 002 — Schema hardening
--
-- Adds, on top of 001_initial_schema.sql:
--   1. CHECK constraints on status/type/category text fields
--   2. Auto-maintained updated_at triggers
--   3. Embedding model versioning (destinations, user_preferences)
--   4. Guest/anonymous interaction tracking (session_id)
--   5. Destination and listing images
--   6. Listing price amount + currency
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CHECK constraints
-- ----------------------------------------------------------------------------

ALTER TABLE raw_scrapes
    ADD CONSTRAINT chk_raw_scrapes_status
    CHECK (status IN ('fetched', 'parsed', 'enriched', 'published', 'failed'));

ALTER TABLE destinations
    ADD CONSTRAINT chk_destinations_status
    CHECK (status IN ('draft', 'enriched', 'published', 'archived'));

ALTER TABLE listings
    ADD CONSTRAINT chk_listings_status
    CHECK (status IN ('pending', 'published', 'archived')),
    ADD CONSTRAINT chk_listings_type
    CHECK (listing_type IN ('hotel', 'hostel', 'airbnb', 'resort', 'other'));

ALTER TABLE user_interactions
    ADD CONSTRAINT chk_user_interactions_type
    CHECK (interaction_type IN ('viewed', 'saved', 'searched', 'booking_click', 'rated'));

ALTER TABLE tags
    ADD CONSTRAINT chk_tags_category
    CHECK (category IN ('vibe', 'activity', 'climate', 'cost', 'other'));

-- Either a user_id or a session_id must be present on an interaction (added
-- after the session_id column is created below — see section 4).

-- ----------------------------------------------------------------------------
-- 2. Auto-maintained updated_at
-- ----------------------------------------------------------------------------

CREATE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_raw_scrapes_updated_at
    BEFORE UPDATE ON raw_scrapes
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_destinations_updated_at
    BEFORE UPDATE ON destinations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_listings_updated_at
    BEFORE UPDATE ON listings
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ----------------------------------------------------------------------------
-- 3. Embedding model versioning
-- ----------------------------------------------------------------------------

ALTER TABLE destinations
    ADD COLUMN embedding_model TEXT,
    ADD COLUMN embedding_updated_at TIMESTAMPTZ;

ALTER TABLE user_preferences
    ADD COLUMN embedding_model TEXT,
    ADD COLUMN embedding_updated_at TIMESTAMPTZ;

-- ----------------------------------------------------------------------------
-- 4. Guest / anonymous interaction tracking
-- ----------------------------------------------------------------------------

ALTER TABLE user_interactions
    ADD COLUMN session_id TEXT;

CREATE INDEX idx_user_interactions_session_id ON user_interactions(session_id);
CREATE INDEX idx_user_interactions_created_at ON user_interactions(created_at);

ALTER TABLE user_interactions
    ADD CONSTRAINT chk_user_interactions_identity
    CHECK (user_id IS NOT NULL OR session_id IS NOT NULL);

-- ----------------------------------------------------------------------------
-- 5. Images
-- ----------------------------------------------------------------------------

CREATE TABLE destination_images (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    destination_id      UUID NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    s3_key              TEXT NOT NULL,
    alt_text            TEXT,
    is_primary          BOOLEAN NOT NULL DEFAULT false,
    sort_order          SMALLINT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_destination_images_destination_id ON destination_images(destination_id);
-- Only one primary image per destination
CREATE UNIQUE INDEX idx_destination_images_one_primary
    ON destination_images(destination_id) WHERE is_primary;

CREATE TABLE listing_images (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id          UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    s3_key              TEXT NOT NULL,
    alt_text            TEXT,
    is_primary          BOOLEAN NOT NULL DEFAULT false,
    sort_order          SMALLINT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_listing_images_listing_id ON listing_images(listing_id);
CREATE UNIQUE INDEX idx_listing_images_one_primary
    ON listing_images(listing_id) WHERE is_primary;

-- ----------------------------------------------------------------------------
-- 6. Listing price
-- ----------------------------------------------------------------------------

ALTER TABLE listings
    ADD COLUMN price_amount NUMERIC(10, 2),
    ADD COLUMN currency CHAR(3) NOT NULL DEFAULT 'USD';
