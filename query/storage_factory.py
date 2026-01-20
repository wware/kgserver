"""
Storage factory for creating and managing storage backend instances.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlmodel import Session
from storage.backends.postgres import PostgresStorage
from storage.backends.sqlite import SQLiteStorage
from storage.interfaces import StorageInterface

# Singleton engine and db_url
_engine = None
_db_url = None


def get_engine():
    """
    Returns a singleton instance of the SQLAlchemy engine and db_url.
    """
    global _engine, _db_url
    if _engine is None:
        _db_url = os.getenv("DATABASE_URL")
        if not _db_url:
            print("DATABASE_URL not set, defaulting to SQLite in-memory database.")
            _db_url = "sqlite:///./test.db"  # Default to SQLite file for simplicity

        connect_args = {}
        if _db_url.startswith("sqlite://"):
            connect_args["check_same_thread"] = False  # Needed for SQLite with FastAPI

        _engine = create_engine(_db_url, connect_args=connect_args)
    return _engine, _db_url


def get_storage() -> Generator[StorageInterface, None, None]:
    """
    FastAPI dependency that provides a storage instance with a request-scoped session.
    """
    engine, db_url = get_engine()  # Get both engine and db_url

    if db_url.startswith("postgresql://"):
        with Session(engine) as session:
            try:
                storage: StorageInterface = PostgresStorage(session)
                yield storage
                session.commit()
            except Exception:
                session.rollback()
                raise
    elif db_url.startswith("sqlite://"):
        # SQLiteStorage manages its own engine/session, so we instantiate it directly.
        # It's important to pass the actual file path or ":memory:".
        db_path = db_url.replace("sqlite:///", "")  # Remove prefix to get path
        if not db_path:  # Handle in-memory or relative path cases
            db_path = ":memory:" if db_url == "sqlite:///:memory:" else "./test.db"

        storage: StorageInterface = SQLiteStorage(db_path)
        try:
            yield storage
            # SQLiteStorage commits internally on operations or doesn't need explicit commit here
            # for read-only usage, but we ensure it's closed.
        finally:
            storage.close()  # Ensure SQLite connection is closed
    else:
        raise ValueError("Unsupported database URL scheme.")


def close_storage():
    """
    Closes the engine connection.
    """
    global _engine, _db_url
    if _engine:
        _engine.dispose()
        _engine = None
        _db_url = None
