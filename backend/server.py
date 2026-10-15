"""Flask API for the observatory pipeline.

Run from backend\\:  python server.py   ->  http://127.0.0.1:5000
"""

from datetime import date
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import func, select, text

from db.models import Image, ObservingSession, Target
from db.session import SessionLocal

DATA_DIR = Path(__file__).resolve().parent / "data"  # where image files live

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])  # Vite dev server


def image_json(img):
    return {
        "id": img.id,
        "url": f"/api/images/{img.id}/file",  # use this as <img src>
        "target": img.target.name if img.target else None,
        "night_of": img.session.night_of.isoformat(),
        "captured_at": img.captured_at.isoformat(),
        "width": img.width,
        "height": img.height,
        "exposure_s": img.exposure_s,
        "sharpness": img.sharpness,
    }


@app.get("/api/health")
def health():
    """Quick check that Flask is up and can reach Postgres."""
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return jsonify({"status": "ok"})


@app.get("/api/images")
def list_images():
    """All images, newest first. Optional: ?target=Moon  ?night=2026-10-12  ?limit=50"""
    query = select(Image).join(Image.session).order_by(Image.captured_at.desc())
    if target := request.args.get("target"):
        query = query.join(Image.target).where(Target.name.ilike(target))
    if night := request.args.get("night"):
        try:
            query = query.where(ObservingSession.night_of == date.fromisoformat(night))
        except ValueError:
            return jsonify({"error": "night must look like 2026-10-12"}), 400
    query = query.limit(min(request.args.get("limit", 100, type=int), 500))

    with SessionLocal() as db:
        return jsonify([image_json(img) for img in db.scalars(query)])


@app.get("/api/images/<int:image_id>")
def get_image(image_id):
    with SessionLocal() as db:
        img = db.get(Image, image_id) or abort(404)
        return jsonify(image_json(img))


@app.get("/api/images/<int:image_id>/file")
def get_image_file(image_id):
    """The picture itself."""
    with SessionLocal() as db:
        img = db.get(Image, image_id) or abort(404)
        return send_from_directory(DATA_DIR, img.file_path)


@app.get("/api/sessions")
def list_sessions():
    """Each observing night with how many images it has."""
    query = (
        select(ObservingSession.night_of, func.count(Image.id))
        .outerjoin(ObservingSession.images)
        .group_by(ObservingSession.id)
        .order_by(ObservingSession.night_of.desc())
    )
    with SessionLocal() as db:
        return jsonify([{"night_of": n.isoformat(), "image_count": c} for n, c in db.execute(query)])


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(port=5000, debug=True)