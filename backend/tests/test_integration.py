
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from db.models import Image, ObservingSession
from db.session import SessionLocal
from server import app, DATA_DIR


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


@pytest.fixture
def test_image():

    unique_id = uuid4().hex

    
    night = date(2099, 1, 1) + timedelta(days=uuid4().int % 36500)
    file_path = f"images/pytest_{unique_id}.jpg"

    full_file_path = DATA_DIR / file_path
    full_file_path.parent.mkdir(parents=True, exist_ok=True)
    full_file_path.write_bytes(b"test image file")

    session = None
    image = None

    try:
        with SessionLocal() as db:
            session = ObservingSession(
                night_of=night,
                started_at=None,
                ended_at=None,
                notes="Temporary integration test"
            )

            db.add(session)
            db.flush()

            image = Image(
                session_id=session.id,
                target_id=None,
                file_path=file_path,
                preview_path=None,
                captured_at=datetime.now(timezone.utc),
                exposure_s=1.0,
                width=1,
                height=1,
                file_size_bytes=len(b"test image file"),
                sharpness=None
            )

            db.add(image)
            db.commit()

            image_id = image.id

        yield {
            "id": image_id,
            "file_path": file_path
        }

    finally:
        with SessionLocal() as db:
            if image is not None:
                db.delete(db.merge(image))

            if session is not None:
                db.delete(db.merge(session))

            db.commit()

        if full_file_path.exists():
            full_file_path.unlink()


def test_get_images(client, test_image):
    response = client.get("/api/images")

    assert response.status_code == 200
    assert response.is_json

    images = response.get_json()
    assert any(img["id"] == test_image["id"] for img in images)


def test_get_existing_image(client, test_image):
    response = client.get(f"/api/images/{test_image['id']}")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json()["id"] == test_image["id"]


def test_get_missing_image(client):
    response = client.get("/api/images/999999999")

    assert response.status_code == 404


def test_get_existing_image_file(client, test_image):
    response = client.get(f"/api/images/{test_image['id']}/file")

    assert response.status_code == 200
    assert response.data == b"test image file"


def test_get_missing_image_file(client):
    response = client.get("/api/images/999999999/file")

    assert response.status_code == 404
