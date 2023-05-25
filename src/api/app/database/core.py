"""
    Database core. Contains engine, ORM related stuff.
"""
from pathlib import Path

# Settings.
from app.config import Settings, get_logger

# Imports.
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import IntegrityError
from alembic.command import upgrade
from alembic.config import Config

from sqlalchemy import create_engine, MetaData

# Settings.
from app.config import get_logger, Settings

# Database engine.
settings = Settings()
engine = create_engine(
    url=settings.database_dsn,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=settings.database_pool_recycle,
    pool_pre_ping=True,
    poolclass=QueuePool,
)
metadata = MetaData(bind=engine)

# Base, session from core.
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=True, bind=engine
)
Base = declarative_base(metadata=metadata)


def create_all(use_sqlalchemy_metadata: bool = False):
    """
    Creates all database metadata by running migrations.
    :param bool use_sqlalchemy_metadata: if True, uses metadata.create_all function instead of migrations 
    """
    if use_sqlalchemy_metadata:
        create_all_with_metadata()
    else:
        create_all_with_migrations()


def create_all_with_metadata():
    """
    Creates all tables using sqlalchemy metadata.
    """
    try:
        metadata.create_all(bind=engine)
    except IntegrityError:
        # TODO: Add logging? (should be there is any circular import?)
        pass


def create_all_with_migrations():
    """
    Create all tables using alembic migrations.
    """
    root_dir = Path().resolve()
    migrations_dir = root_dir / "migrations"
    config_file = root_dir / "alembic.ini"

    config = Config(file_=config_file)
    config.set_main_option("script_location", str(migrations_dir))

    upgrade(config, "head")

