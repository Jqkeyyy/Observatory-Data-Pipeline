"""
Routes to create, list, and delete session jobs (what the Pi should capture),
plus the routes the Observatory Pi calls: polling for work, reporting status,
and uploading the finished pictures.

    Admin page:  POST   /api/sessions/jobs
                 GET    /api/sessions/jobs?status=pending
                 DELETE /api/sessions/jobs/<id>
    Pi:          GET    /api/sessions/jobs/next-pending
                 POST   /api/sessions/jobs/<id>/ack
                 POST   /api/sessions/jobs/upload
"""

import io
import re
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, jsonify, request
from PIL import Image as PILImage
from PIL import UnidentifiedImageError
from sqlalchemy import func, or_, select, text
from werkzeug.utils import secure_filename

from db.models import Image, ObservingSession, SessionJob
from db.session import SessionLocal

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions/jobs")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

TZ = ZoneInfo("America/Chicago")  # observatory time
DEVICE_ID = "observatory_pi_1"  # only one Pi for now
MIN_INTERVAL_S = 30  # Dr. Nine: no more than ~2 pictures a minute (the database enforces this too)
ACTIVE_STATUSES = ("pending", "running")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
THUMB_SIZE = (960, 540)
FRAME_NAME = re.compile(r"frame_(\d{9,})_")  # the Pi names pictures frame_<unix time>_<n>.jpg


def parse_time(value):
    """ISO 8601 -> datetime. Times without a timezone are observatory time."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=TZ)


def clock(dt):
    """'Thu Nov 12, 9:00 PM' in observatory time."""
    local = dt.astimezone(TZ)
    return f"{local:%a %b} {local.day}, {local:%I:%M %p}".replace(" 0", " ")


def job_window(job):
    """(start, end) of a job. A job with no scheduled time starts when the Pi picks it up."""
    start = job.scheduled_for or job.started_at or job.created_at
    return start, start + timedelta(seconds=job.duration_seconds)


@sessions_bp.post("")
def create_session_job():
    """Create a new pending job from the admin form, refusing ones that overlap another job."""
    data = request.get_json(silent=True) or request.form

    try:
        duration = int(data.get("duration_seconds", 0))
        interval = int(data.get("interval_seconds", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "duration_seconds and interval_seconds must be integers"}), 400

    if duration <= 0:
        return jsonify({"error": "Duration must be greater than 0."}), 400
    if interval < MIN_INTERVAL_S:
        return jsonify({"error": f"Interval must be at least {MIN_INTERVAL_S} seconds (2 pictures a minute at most)."}), 400

    now = datetime.now(timezone.utc)
    scheduled_for = None
    scheduled_raw = data.get("scheduled_for") or data.get("scheduled_at")
    if scheduled_raw:
        try:
            scheduled_for = parse_time(scheduled_raw)
        except (ValueError, TypeError, AttributeError):
            return jsonify({"error": "Invalid datetime format for scheduled_for. Use ISO 8601."}), 400
        if scheduled_for < now - timedelta(minutes=1):
            return jsonify({"error": "Scheduled time is in the past."}), 400

    new_start = scheduled_for or now
    new_end = new_start + timedelta(seconds=duration)

    with SessionLocal() as db:
        # Only one request can check-and-insert at a time, so two people clicking at once
        # can't both pass the overlap check. Postgres releases the lock at commit/rollback.
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext('session_job'))"))

        active_jobs = db.scalars(
            select(SessionJob).where(
                SessionJob.device_id == DEVICE_ID,
                SessionJob.status.in_(ACTIVE_STATUSES),
            )
        ).all()
        for job in active_jobs:
            start, end = job_window(job)
            if new_start < end and new_end > start:  # (StartA < EndB) and (EndA > StartB)
                return jsonify({
                    "error": f"That overlaps job #{job.id} ({clock(start)} to {clock(end)}).",
                    "conflict": job.to_dict(),
                }), 409

        new_job = SessionJob(
            device_id=DEVICE_ID,
            duration_seconds=duration,
            interval_seconds=interval,
            scheduled_for=scheduled_for,
            status="pending",
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        return jsonify(new_job.to_dict()), 201


@sessions_bp.get("")
def get_session_jobs():
    """Get session jobs with optional status filter: ?status=pending"""
    status_filter = request.args.get("status")

    with SessionLocal() as db:
        query = select(SessionJob).order_by(SessionJob.created_at.desc())

        if status_filter:
            query = query.where(SessionJob.status == status_filter.lower())

        jobs = db.scalars(query).all()
        return jsonify([job.to_dict() for job in jobs]), 200


@sessions_bp.get("/next-pending")
def get_next_pending_job():
    """Polled by the Raspberry Pi. Returns a ready job, or the time of the next upcoming job."""
    now_utc = datetime.now(timezone.utc)

    with SessionLocal() as db:
        ready_query = (
            select(SessionJob)
            .where(
                SessionJob.device_id == DEVICE_ID,
                SessionJob.status == "pending",
                or_(
                    SessionJob.scheduled_for.is_(None),
                    SessionJob.scheduled_for <= now_utc,
                ),
            )
            .order_by(func.coalesce(SessionJob.scheduled_for, SessionJob.created_at).asc())
            .limit(1)
        )
        job = db.scalars(ready_query).first()
        if job:
            return jsonify(job.to_dict()), 200

        future_query = (
            select(SessionJob)
            .where(
                SessionJob.device_id == DEVICE_ID,
                SessionJob.status == "pending",
                SessionJob.scheduled_for > now_utc,
            )
            .order_by(SessionJob.scheduled_for.asc())
            .limit(1)
        )
        future_job = db.scalars(future_query).first()

        if future_job:
            # give pi timestamp for next job
            return jsonify({
                "status": "idle",
                "next_scheduled_for": future_job.scheduled_for.isoformat(),
            }), 200

        return jsonify({"status": "idle"}), 200


@sessions_bp.post("/<int:job_id>/ack")
def acknowledge_job(job_id):
    """The Pi calls this to update status: 'running', 'completed', or 'error'."""
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    if new_status not in ("running", "completed", "error"):
        return jsonify({"error": "status must be 'running', 'completed', or 'error'"}), 400

    with SessionLocal() as db:
        job = db.get(SessionJob, job_id) or abort(404)
        job.status = new_status

        if new_status == "running":
            job.started_at = func.now()
        elif new_status in ("completed", "error"):
            job.completed_at = func.now()

        db.commit()
        return jsonify(job.to_dict()), 200


@sessions_bp.delete("/<int:job_id>")
def delete_session_job(job_id):
    """Delete a specific session job by its ID."""
    with SessionLocal() as db:
        job = db.get(SessionJob, job_id) or abort(404)
        db.delete(job)
        db.commit()
        return jsonify({"status": "success", "message": f"Job {job_id} deleted successfully"}), 200


def captured_time(info):
    """When a picture was taken: from the Pi's file name, else the time stored in the zip."""
    if match := FRAME_NAME.match(Path(info.filename).name):
        return datetime.fromtimestamp(int(match.group(1)), tz=timezone.utc)
    return datetime(*info.date_time, tzinfo=TZ)


def night_of(captured):
    """After-midnight pictures count as the night before (same rule as load_sample_images.py)."""
    return (captured.astimezone(TZ) - timedelta(hours=12)).date()


def pixel_size(data):
    try:
        with PILImage.open(io.BytesIO(data)) as img:
            return img.size
    except (UnidentifiedImageError, OSError):
        return None, None


def make_thumbnail(name, data):
    """A 960x540 preview, for pictures the Pi didn't send one for. Returns its file name."""
    thumb_name = f"thumb_{Path(name).stem}.jpg"
    try:
        with PILImage.open(io.BytesIO(data)) as img:
            img.thumbnail(THUMB_SIZE)
            img.convert("RGB").save(THUMBNAILS_DIR / thumb_name, "JPEG", quality=85)
    except (UnidentifiedImageError, OSError):
        return None
    return thumb_name


@sessions_bp.post("/upload")
def upload_observing_session():
    """
    Receives one finished job from the Observatory Pi:
        form field "job_id", file "archive" (zip of full-size pictures),
        files "thumbnails" (960x540 previews named thumb_<picture name>).
    The pictures join that night's ObservingSession, stored in data/sessions/session_<id>.zip,
    and the thumbnails go to data/thumbnails.
    """
    try:
        job_id = int(request.form.get("job_id") or request.form.get("session_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "job_id is required and must be an integer"}), 400

    archive = request.files.get("archive")
    if not archive:
        return jsonify({"error": "No session zip file provided (send it as 'archive')"}), 400

    with tempfile.TemporaryDirectory(dir=DATA_DIR) as tmp:
        upload_path = Path(tmp) / "upload.zip"
        archive.save(upload_path)
        try:
            source = zipfile.ZipFile(upload_path)
        except zipfile.BadZipFile:
            return jsonify({"error": "archive is not a zip file"}), 400

        with source:
            pictures = [
                info for info in source.infolist()
                if not info.is_dir() and info.filename.lower().endswith(IMAGE_EXTENSIONS)
            ]
            if not pictures:
                return jsonify({"error": "The zip has no pictures in it"}), 400
            pictures.sort(key=captured_time)

            # Never trust names from the request: secure_filename strips folders and "..",
            # so nothing can be written outside data/.
            thumbnails = {}
            for thumb in request.files.getlist("thumbnails"):
                thumb_name = secure_filename(thumb.filename or "")
                if thumb_name.startswith("thumb_"):
                    thumb.save(THUMBNAILS_DIR / thumb_name)
                    thumbnails[thumb_name.removeprefix("thumb_")] = thumb_name

            with SessionLocal() as db:
                # One upload at a time, so two never write to the same zip at once
                db.execute(text("SELECT pg_advisory_xact_lock(hashtext('session_upload'))"))

                first, last = captured_time(pictures[0]), captured_time(pictures[-1])
                night = night_of(first)
                observing_session = db.scalar(select(ObservingSession).where(ObservingSession.night_of == night))
                if not observing_session:
                    observing_session = ObservingSession(night_of=night)
                    db.add(observing_session)
                    db.flush()
                observing_session.started_at = min(filter(None, [observing_session.started_at, first]))
                observing_session.ended_at = max(filter(None, [observing_session.ended_at, last]))

                zip_path = SESSIONS_DIR / f"session_{observing_session.id}.zip"
                added = 0
                with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_DEFLATED) as session_zip:
                    in_zip = set(session_zip.namelist())
                    for info in pictures:
                        name = secure_filename(Path(info.filename).name)
                        file_path = f"sessions/{zip_path.name}/{name}"
                        if db.scalar(select(Image.id).where(Image.file_path == file_path)):
                            continue  # already uploaded (the Pi retried)

                        data = source.read(info)
                        if name not in in_zip:
                            session_zip.writestr(name, data)
                            in_zip.add(name)

                        width, height = pixel_size(data)
                        db.add(Image(
                            session_id=observing_session.id,
                            file_path=file_path,
                            preview_path=thumbnails.get(name) or make_thumbnail(name, data),
                            captured_at=captured_time(info),
                            width=width,
                            height=height,
                            file_size_bytes=len(data),
                            meta={"source": "pi", "job_id": job_id},
                        ))
                        added += 1

                db.commit()
                session_id = observing_session.id

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "night_of": night.isoformat(),
        "images_added": added,
        "message": f"Job {job_id}: {added} pictures added to the {night.isoformat()} session.",
    }), 201
