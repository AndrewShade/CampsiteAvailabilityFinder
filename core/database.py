from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args)
    return _engine


def init_db():
    from . import models  # noqa: F401 — registers models with Base
    Base.metadata.create_all(bind=_get_engine())
    _migrate()


def _migrate():
    """Add columns introduced after the initial schema without wiping data."""
    new_columns = [
        ("watchlist_entries", "check_in_day", "TEXT"),
        ("watchlist_entries", "check_out_day", "TEXT"),
        ("watchlist_entries", "max_nights", "INTEGER"),
    ]
    with _get_engine().connect() as conn:
        for table, column, col_type in new_columns:
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            if column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                conn.commit()


@contextmanager
def get_db():
    db = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())()
    try:
        yield db
    finally:
        db.close()
