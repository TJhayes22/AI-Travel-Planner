"""
Revision 0001: Initial schema

Created tables:
- users
- user_preferences
- raw_scrapes
- destinations
- tags
- destination_tags
- listings
- user_interactions
- itineraries

Plus extensions (vector, pg_trgm, pgcrypto) and search_vector trigger.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema."""
    
    # Create extensions (pgcrypto is required for gen_random_uuid())
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("auth_provider_id", sa.TEXT(), nullable=False),
        sa.Column("email", sa.TEXT(), nullable=False),
        sa.Column("display_name", sa.TEXT(), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("auth_provider_id"),
        sa.UniqueConstraint("email"),
    )
    
    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_input", sa.TEXT(), nullable=True),
        sa.Column("structured_tags", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("embedding", Vector(dim=1536), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    
    # Create raw_scrapes table
    op.create_table(
        "raw_scrapes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("source_name", sa.TEXT(), nullable=False),
        sa.Column("source_url", sa.TEXT(), nullable=False),
        sa.Column("s3_raw_key", sa.TEXT(), nullable=False),
        sa.Column("content_hash", sa.TEXT(), nullable=False),
        sa.Column("parsed_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.TEXT(), server_default=sa.text("'fetched'::text"), nullable=False),
        sa.Column("error_message", sa.TEXT(), nullable=True),
        sa.Column("fetched_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_raw_scrapes_status", "raw_scrapes", ["status"])
    op.create_index("idx_raw_scrapes_content_hash", "raw_scrapes", ["content_hash"])
    
    # Create destinations table
    op.create_table(
        "destinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("raw_scrape_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.TEXT(), nullable=False),
        sa.Column("slug", sa.TEXT(), nullable=False),
        sa.Column("country", sa.TEXT(), nullable=True),
        sa.Column("region", sa.TEXT(), nullable=True),
        sa.Column("latitude", sa.DOUBLE_PRECISION(), nullable=True),
        sa.Column("longitude", sa.DOUBLE_PRECISION(), nullable=True),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("cost_tier", sa.SMALLINT(), nullable=True),
        sa.Column("climate", sa.TEXT(), nullable=True),
        sa.Column("best_season", sa.TEXT(), nullable=True),
        sa.Column("source_url", sa.TEXT(), nullable=True),
        sa.Column("status", sa.TEXT(), server_default=sa.text("'draft'::text"), nullable=False),
        sa.Column("embedding", Vector(dim=1536), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["raw_scrape_id"], ["raw_scrapes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("idx_destinations_status", "destinations", ["status"])
    op.create_index(
        "idx_destinations_search_vector",
        "destinations",
        ["search_vector"],
        postgresql_using="gin",
    )
    # HNSW vector index for similarity search
    op.create_index(
        "idx_destinations_embedding",
        "destinations",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    
    # Create tags table
    op.create_table(
        "tags",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("name", sa.TEXT(), nullable=False),
        sa.Column("category", sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    
    # Create destination_tags table
    op.create_table(
        "destination_tags",
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", sa.INTEGER(), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("destination_id", "tag_id"),
    )
    op.create_index("idx_destination_tags_tag_id", "destination_tags", ["tag_id"])
    
    # Create listings table
    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.TEXT(), nullable=False),
        sa.Column("listing_type", sa.TEXT(), nullable=False),
        sa.Column("price_tier", sa.SMALLINT(), nullable=True),
        sa.Column("rating", sa.NUMERIC(precision=2, scale=1), nullable=True),
        sa.Column("booking_url", sa.TEXT(), nullable=False),
        sa.Column("affiliate_id", sa.TEXT(), nullable=True),
        sa.Column("source_name", sa.TEXT(), nullable=True),
        sa.Column("status", sa.TEXT(), server_default=sa.text("'published'::text"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_listings_destination_id", "listings", ["destination_id"])
    
    # Create user_interactions table
    op.create_table(
        "user_interactions",
        sa.Column("id", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("interaction_type", sa.TEXT(), nullable=False),
        sa.Column("rating", sa.SMALLINT(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_interactions_user_id", "user_interactions", ["user_id"])
    op.create_index("idx_user_interactions_destination_id", "user_interactions", ["destination_id"])
    op.create_index("idx_user_interactions_type", "user_interactions", ["interaction_type"])
    
    # Create itineraries table
    op.create_table(
        "itineraries",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cache_key", sa.TEXT(), nullable=False),
        sa.Column("input_params", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("generated_content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cache_key"),
    )
    op.create_index("idx_itineraries_user_id", "itineraries", ["user_id"])
    
    # Create trigger function for search_vector maintenance
    op.execute("""
        CREATE FUNCTION destinations_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.region, '') || ' ' || coalesce(NEW.country, '')), 'C');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger on destinations
    op.execute("""
        CREATE TRIGGER trg_destinations_search_vector
            BEFORE INSERT OR UPDATE ON destinations
            FOR EACH ROW EXECUTE FUNCTION destinations_search_vector_update();
    """)


def downgrade() -> None:
    """Drop initial schema in reverse dependency order."""
    
    # Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trg_destinations_search_vector ON destinations")
    op.execute("DROP FUNCTION IF EXISTS destinations_search_vector_update()")
    
    # Drop tables in reverse dependency order (tables that reference others first)
    op.drop_table("itineraries")
    op.drop_table("user_interactions")
    op.drop_table("destination_tags")
    op.drop_table("tags")
    op.drop_table("listings")
    op.drop_table("destinations")
    op.drop_table("raw_scrapes")
    op.drop_table("user_preferences")
    op.drop_table("users")
    
    # Note: Extensions (pgcrypto, pg_trgm, vector) are left in place as they
    # require superuser privileges to drop and are system-level resources
    # that should persist across migrations.
