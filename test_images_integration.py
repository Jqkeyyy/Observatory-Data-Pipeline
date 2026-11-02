
import pytest
from server import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_get_images(client):
    """The API should retrieve image records."""
    response = client.get("/api/images")

    assert response.status_code == 200
    assert response.is_json


def test_get_existing_image(client):
    """The API should return an existing database record."""
    response = client.get("/api/images/1")

    assert response.status_code == 200
    assert response.is_json


def test_get_missing_image(client):
    """A nonexistent image should return 404."""
    response = client.get("/api/images/999999")

    assert response.status_code == 404


def test_get_existing_image_file(client):
    """The API should return the image file from disk."""
    response = client.get("/api/images/1/file")

    assert response.status_code == 200
    assert len(response.data) > 0


def test_get_missing_image_file(client):
    """A nonexistent image should return 404."""
    response = client.get("/api/images/999999/file")

    assert response.status_code == 404
