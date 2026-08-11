"""add source/attribution fields to destination_images

Revision ID: 0003
Revises: 0002
Create Date: (fill in)
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("destination_images", sa.Column("source_url", sa.Text(), nullable=True))
    op.add_column("destination_images", sa.Column("source_name", sa.Text(), nullable=True))
    op.add_column("destination_images", sa.Column("attribution", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("destination_images", "attribution")
    op.drop_column("destination_images", "source_name")
    op.drop_column("destination_images", "source_url")