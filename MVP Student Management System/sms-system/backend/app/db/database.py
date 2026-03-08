"""
Database Module

Handles database connection, session management, and base model configuration.
Uses SQLAlchemy 2.0 async ORM patterns.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


# Determine if we're using SQLite
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Create engine with appropriate configuration
if is_sqlite:
    # SQLite specific configuration for development
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,
        max_overflow=20,
        echo=settings.DEBUG,
    )


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.
    
    Yields:
        SQLAlchemy Session object
        
    Usage:
        Use as a FastAPI dependency:
        
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This should be called once at application startup.
    In production, use Alembic migrations instead.
    """
    try:
        # Import all models to ensure they're registered
        from app.models import (
            user,
            student_profile,
            lecturer,
            module,
            enrollment,
            timetable,
            attendance,
            assignment,
            announcement,
            result,
            ticket,
            supplier,
            campus_map,
        )
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def close_db() -> None:
    """Close database connections."""
    engine.dispose()
    logger.info("Database connections closed")


# SQLite foreign key support
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key support for SQLite."""
    if is_sqlite:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
