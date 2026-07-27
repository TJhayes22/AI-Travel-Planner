"""
Revision 0002: Schema hardening

Builds on 0001 by adding:
1. CHECK constraints on status/type/category fields
2. Auto-maintained updated_at triggers
3. Embedding model versioning columns
4. Guest/anonymous interaction tracking (session_id)
5. Destination and listing images tables
6. Listing price amount + currency
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply schema hardening."""
    
    # 1. Add CHECK constraints to existing tables
    op.execute("""
        ALTER TABLE raw_scrapes
            ADD CONSTRAINT chk_raw_scrapes_status
            CHECK (status IN ('fetched', 'parsed', 'enriched', 'published', 'failed'))
    """)
    
    op.execute("""
        ALTER TABLE destinations
            ADD CONSTRAINT chk_destinations_status
            CHECK (status IN ('draft', 'enriched', 'published', 'archived'))
    """)
    
    op.execute("""
        ALTER TABLE listings
            ADD CONSTRAINT chk_listings_status
            CHECK (status IN ('pending', 'published', 'archived')),
            ADD CONSTRAINT chk_listings_type
            CHECK (listing_type IN ('hotel', 'hostel', 'airbnb', 'resort', 'other'))
    """)
    
    op.execute("""
        ALTER TABLE user_interactions
            ADD CONSTRAINT chk_user_interactions_type
            CHECK (interaction_type IN ('viewed', 'saved', 'searched', 'booking_click', 'rated'))
    """)
    
    op.execute("""
        ALTER TABLE tags
            ADD CONSTRAINT chk_tags_category
            CHECK (category IN ('vibe', 'activity', 'climate', 'cost', 'other'))
    """)
    
    # 2. Create set_updated_at() trigger function (used by multiple tables)
    op.execute("""
        CREATE FUNCTION set_updated_at() RETURNS trigger AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql
    """)
    
    # Create triggers on tables with updated_at columns
    op.execute("""
        CREATE TRIGGER trg_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)
    
    op.execute("""
        CREATE TRIGGER trg_user_preferences_updated_at
            BEFORE UPDATE ON user_preferences
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)
    
    op.execute("""
        CREATE TRIGGER trg_raw_scrapes_updated_at
            BEFORE UPDATE ON raw_scrapes
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)
    
    op.execute("""
        CREATE TRIGGER trg_destinations_updated_at
            BEFORE UPDATE ON destinations
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)
    
    op.execute("""
        CREATE TRIGGER trg_listings_updated_at
            BEFORE UPDATE ON listings
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)
    
    # 3. Add embedding model versioning columns
    op.add_column(
        "destinations",
        sa.Column("embedding_model", sa.TEXT(), nullable=True),
    )
    op.add_column(
        "destinations",
        sa.Column("embedding_updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    
    op.add_column(
        "user_preferences",
        sa.Column("embedding_model", sa.TEXT(), nullable=True),
    )
    op.add_column(
        "user_preferences",
        sa.Column("embedding_updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    
    # 4. Add session_id column for guest interactions
    op.add_column(
        "user_interactions",
        sa.Column("session_id", sa.TEXT(), nullable=True),
    )
    
    op.create_index(
        "idx_user_interactions_session_id",
        "user_interactions",
        ["session_id"],
    )
    
    op.create_index(
        "idx_user_interactions_created_at",
        "user_interactions",
        ["created_at"],
    )
    
    # Add constraint: either user_id or session_id must be present
    op.execute("""
        ALTER TABLE user_interactions
            ADD CONSTRAINT chk_user_interactions_identity
            CHECK (user_id IS NOT NULL OR session_id IS NOT NULL)
    """)
    
    # 5. Create destination_images table
    op.create_table(
        "destination_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("s3_key", sa.TEXT(), nullable=False),
        sa.Column("alt_text", sa.TEXT(), nullable=True),
        sa.Column("is_primary", sa.BOOLEAN(), server_default=sa.text("false"), nullable=False),
        sa.Column("sort_order", sa.SMALLINT(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    
    op.create_index(
        "idx_destination_images_destination_id",
        "destination_images",
        ["destination_id"],
    )
    
    # Unique index: only one primary image per destination
    op.create_index(
        "idx_destination_images_one_primary",
        "destination_images",
        ["destination_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )
    
    # Create listing_images table
    op.create_table(
        "listing_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("s3_key", sa.TEXT(), nullable=False),
        sa.Column("alt_text", sa.TEXT(), nullable=True),
        sa.Column("is_primary", sa.BOOLEAN(), server_default=sa.text("false"), nullable=False),
        sa.Column("sort_order", sa.SMALLINT(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    
    op.create_index(
        "idx_listing_images_listing_id",
        "listing_images",
        ["listing_id"],
    )
    
    # Unique index: only one primary image per listing
    op.create_index(
        "idx_listing_images_one_primary",
        "listing_images",
        ["listing_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )
    
    # 6. Add price columns to listings
    op.add_column(
        "listings",
        sa.Column("price_amount", sa.NUMERIC(precision=10, scale=2), nullable=True),
    )
    op.add_column(
        "listings",
        sa.Column("currency", sa.CHAR(length=3), server_default=sa.text("'USD'::bpchar"), nullable=False),
    )


def downgrade() -> None:
    """Remove schema hardening changes (only changes from this migration, not from 0001)."""
    
    # 1. Drop price columns from listings
    op.drop_column("listings", "currency")
    op.drop_column("listings", "price_amount")
    
    # 2. Drop image tables
    op.drop_table("listing_images")
    op.drop_table("destination_images")
    
    # 3. Remove session_id and related from user_interactions
    op.drop_constraint("chk_user_interactions_identity", "user_interactions", type_="check")
    op.drop_index("idx_user_interactions_created_at", table_name="user_interactions")
    op.drop_index("idx_user_interactions_session_id", table_name="user_interactions")
    op.drop_column("user_interactions", "session_id")
    
    # 4. Remove embedding versioning columns
    op.drop_column("user_preferences", "embedding_updated_at")
    op.drop_column("user_preferences", "embedding_model")
    op.drop_column("destinations", "embedding_updated_at")
    op.drop_column("destinations", "embedding_model")
    
    # 5. Drop updated_at triggers
    op.execute("DROP TRIGGER trg_listings_updated_at ON listings")
    op.execute("DROP TRIGGER trg_destinations_updated_at ON destinations")
    op.execute("DROP TRIGGER trg_raw_scrapes_updated_at ON raw_scrapes")
    op.execute("DROP TRIGGER trg_user_preferences_updated_at ON user_preferences")
    op.execute("DROP TRIGGER trg_users_updated_at ON users")
    op.execute("DROP FUNCTION set_updated_at()")
    
    # 6. Drop CHECK constraints
    op.drop_constraint("chk_tags_category", "tags", type_="check")
    op.drop_constraint("chk_user_interactions_type", "user_interactions", type_="check")
    op.drop_constraint("chk_listings_type", "listings", type_="check")
    op.drop_constraint("chk_listings_status", "listings", type_="check")
    op.drop_constraint("chk_destinations_status", "destinations", type_="check")
    op.drop_constraint("chk_raw_scrapes_status", "raw_scrapes", type_="check")
