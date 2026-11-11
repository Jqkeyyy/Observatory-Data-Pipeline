"""Flask API for the observatory pipeline.

Run from backend\\:  python server.py   ->  http://127.0.0.1:5000
"""

import io
import zipfile
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from sqlalchemy import func, select, text
from routes.sessions import sessions_bp

from db.models import Image, ObservingSession, Target
from db.session import SessionLocal


DATA_DIR = Path(__file__).resolve().parent / "data"
EDITABLE_IMAGE_FIELDS = {"target", "exposure_s", "sharpness", "tags"}
SESSIONS_DIR = DATA_DIR / "sessions"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])
app.register_blueprint(sessions_bp)

def image_json(img):
    return {
        "id": img.id,
        "url": f"/api/images/{img.id}/thumbnail",
        "original_url": f"/api/images/{img.id}/original",
        "target": img.target.name if img.target else None,
        "night_of": img.session.night_of.isoformat(),
        "captured_at": img.captured_at.isoformat(),
        "width": img.width,
        "height": img.height,
        "exposure_s": img.exposure_s,
        "sharpness": img.sharpness,
        "tags": img.tags,
    }


@app.get("/api/health")
def health():
    """Quick check that Flask is up and can reach Postgres."""
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return jsonify({"status": "ok"})


@app.get("/api/images/thumbnails")
def list_thumbnails():
    """Lists all images from the database with both thumbnail and original URLs."""
    with SessionLocal() as db:
        images = db.scalars(select(Image).order_by(Image.captured_at.desc())).all()
        results = []
        for img in images:
            if not img.preview_path:
                continue
            results.append({
                "id": img.id,
                "filename": img.preview_path,
                "url": f"/api/images/{img.id}/thumbnail",
                "original_url": f"/api/images/{img.id}/original",
                "target": img.target.name if img.target else "Unknown",
                "night_of": img.session.night_of.isoformat() if img.session else None
            })
        return jsonify(results), 200

@app.get("/api/images/<int:image_id>/thumbnail")
def get_image_thumbnail(image_id):
    """Serves the lightweight 960x540 web preview for grid cards."""
    with SessionLocal() as db:
        img = db.get(Image, image_id) or abort(404)
        if not img.preview_path:
            abort(404)
            
        filename = Path(img.preview_path).name
        return send_from_directory(THUMBNAILS_DIR, filename)

@app.get("/api/thumbnails/<path:filename>")
def serve_thumbnail(filename):
    """Serves individual web thumbnail files directly from THUMBNAILS_DIR."""
    if not THUMBNAILS_DIR.exists():
        abort(404)
    return send_from_directory(THUMBNAILS_DIR, filename)


@app.get("/api/images/<int:image_id>/original")
def get_image_original(image_id):
    """Extracts and streams the full 4K frame from the session zip on-demand when user full-screens."""
    with SessionLocal() as db:
        img = db.get(Image, image_id) or abort(404)
        
        zip_path = SESSIONS_DIR / f"session_{img.session_id}.zip"
        if not zip_path.exists():
            abort(404)
            
        inner_filename = Path(img.file_path).name
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                if inner_filename not in zf.namelist():
                    abort(404)
                file_data = zf.read(inner_filename)
                return send_file(
                    io.BytesIO(file_data),
                    mimetype="image/jpeg",
                    download_name=inner_filename
                )
        except Exception:
            abort(500)


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


@app.get("/api/tags")
def list_tags():
    """Every tag in use with how many images have it, most used first."""
    tag = func.unnest(Image.tags).label("tag")
    query = select(tag, func.count()).select_from(Image).group_by("tag").order_by(func.count().desc(), "tag")
    with SessionLocal() as db:
        return jsonify([{"tag": t, "count": c} for t, c in db.execute(query)])
    

@app.route("/api/images/<int:image_id>", methods=["PATCH", "PUT"])
def update_image(image_id):
    """Change an image's details. Send only what you want to change, e.g. {"target": "Moon"}
    target: an existing target name, or null to clear it.  exposure_s / sharpness: a number or null.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "send a JSON object with the fields to change"}), 400
    if unknown := sorted(data.keys() - EDITABLE_IMAGE_FIELDS):
        return jsonify({"error": f"can't edit: {', '.join(unknown)}", "editable": sorted(EDITABLE_IMAGE_FIELDS)}), 400
    for field in ("exposure_s", "sharpness"):
        value = data.get(field)
        if field in data and value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
            return jsonify({"error": f"{field} must be a number or null"}), 400

    with SessionLocal() as db:
        img = db.get(Image, image_id) or abort(404)
        if "target" in data:
            name = data["target"]
            if name is None:
                img.target = None
            elif not isinstance(name, str):
                return jsonify({"error": "target must be a name like \"Moon\" or null"}), 400
            else:
                target = db.scalar(select(Target).where(func.lower(Target.name) == name.strip().lower()))
                if target is None:
                    return jsonify({"error": f"no target named {name!r}"}), 400
                img.target = target
        for field in ("exposure_s", "sharpness"):
            if field in data:
                setattr(img, field, data[field])
        if "tags" in data:
            tags = data["tags"]
            if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
                return jsonify({"error": 'tags must be a list like ["clouds", "blurry"]'}), 400
            img.tags = sorted({t.strip().lower() for t in tags if t.strip()})
        db.commit()
        return jsonify(image_json(img))


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