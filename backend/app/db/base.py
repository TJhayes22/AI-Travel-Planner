"""
SQLAlchemy declarative base for all models.

When models are created, they should inherit from Base.metadata.
This module is imported by alembic/env.py for Alembic's autogenerate functionality
(though our migrations are hand-written).
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
