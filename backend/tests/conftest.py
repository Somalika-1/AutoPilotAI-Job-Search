import pytest
from sqlalchemy import text

from app.database import SessionLocal


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Deletes every row created during a test, so the dev DB doesn't accumulate
    test users/resumes/matches on every run. Records the highest `users.id` before
    the test, then deletes every user above that watermark afterward - cascade
    deletes (see the CASCADE migration) take care of their resumes, job
    descriptions, and matches automatically.
    """
    db = SessionLocal()
    watermark = db.execute(text("SELECT COALESCE(MAX(id), 0) FROM users")).scalar()
    db.close()

    yield

    db = SessionLocal()
    db.execute(text("DELETE FROM users WHERE id > :watermark"), {"watermark": watermark})
    db.commit()
    db.close()
