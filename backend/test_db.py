"""Quick database check. Run from backend\\:  python test_db.py
Nothing is kept: everything is rolled back at the end."""
from datetime import date, datetime, timezone

from sqlalchemy import select

from db.models import Image, ObservingSession, Target
from db.session import SessionLocal

with SessionLocal() as db:
    # Save a session, target, and image linked together
    db.add(Image(
        session=ObservingSession(night_of=date(1999, 12, 30)),
        target=Target(name="TEST Moon", type="moon"),
        file_path="test/not-a-real-file.png",
        captured_at=datetime(1999, 12, 31, 3, 0, tzinfo=timezone.utc),
        meta={"camera": "test-webcam"},
    ))
    db.flush()
    db.expire_all()  # forget what's in memory so the checks below read from Postgres

    # Read it back and follow the links
    image = db.scalar(select(Image).where(Image.file_path == "test/not-a-real-file.png"))
    assert image.session.night_of == date(1999, 12, 30)
    assert image.target.name == "TEST Moon"
    assert image.meta["camera"] == "test-webcam"
    assert image.ingested_at is not None

    db.rollback()

print("Database works.")