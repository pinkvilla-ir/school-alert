from contextlib import contextmanager
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Simple DB context helper for tests and local dev.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sravz@localhost:5432/school_alert")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_db_context():
    """Yield a SQLAlchemy session.

    Usage:
        with get_db_context() as db:
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
