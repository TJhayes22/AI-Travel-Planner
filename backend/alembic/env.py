"""
Alembic environment configuration for PostgreSQL + SQLAlchemy.

This module:
1. Reads DATABASE_URL from environment
2. Creates a synchronous SQLAlchemy engine (for migration running)
3. Runs migrations in online mode
"""

import logging
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# this is the Alembic Config object, which provides the values of the parameters
# configured in the ini file, as well as other functions that assist in
# performing database operations and Python-style upgrades and downgrades.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers effectively as per the file's directives.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# add your model's MetaData object here for 'autogenerate' support.
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Import Base and all models for Alembic's autogenerate to see the full schema
try:
    from app.db.base import Base
    # Import all models to populate Base.metadata for autogenerate
    import app.models  # noqa: F401
    target_metadata = Base.metadata
except ImportError:
    # If models don't exist yet, we'll use None (hand-written migrations)
    target_metadata = None


def get_database_url() -> str:
    """Get database URL from environment."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable not set. "
            "Set it with: export DATABASE_URL='postgresql://user:password@localhost/dbname'"
        )
    
    # Convert asyncpg URL to psycopg2/3 for synchronous migrations
    if "postgresql+asyncpg://" in url:
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine, though an Engine
    is acceptable here as well. By skipping the Engine creation we avoid dealing with
    an event listener that must be implemented in order to support the
    "begin_transaction" keyword with asynchronous drivers.
    
    (Not currently used, but kept for completeness.)
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()



def run_migrations_online() -> None:
    """Run migrations in 'online' mode (synchronous).
    
    In this scenario we create a standard Engine and associate a connection
    with the context.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        echo=False,
    )

    with connectable.begin() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    logger.info("Running migrations in offline mode")
    run_migrations_offline()
else:
    logger.info("Running migrations in online mode")
    run_migrations_online()
