import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify, abort
from sqlalchemy import select, func
from db.session import SessionLocal
from db.models import SessionJob, ObservingSession, Image

"""
This file contains routes to create, delete, and update session jobs,
as well as handling session package uploads from the Observatory Pi.
"""

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions/jobs")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)


@sessions_bp.post("")
def create_session_job():
    """Create a new pending job from the frontend form with optional scheduling and conflict detection."""
    data = request.get_json(silent=True) or request.form
    
    try:
        duration = int(data.get("duration_seconds", 0))
        interval = int(data.get("interval_seconds", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "duration_seconds and interval_seconds must be integers"}), 400

    if duration <= 0 or interval <= 0:
        return jsonify({"error": "duration and interval must be greater than 0"}), 400

    scheduled_for_dt = None
    scheduled_raw = data.get("scheduled_for") or data.get("scheduled_at")
    if scheduled_raw:
        try:
            scheduled_for_dt = datetime.fromisoformat(scheduled_raw.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid datetime format for scheduled_for. Use ISO 8601."}), 400

    with SessionLocal() as db:
        # If this job is scheduled, check for time window conflicts with existing pending/running jobs
        if scheduled_for_dt:
            new_start = scheduled_for_dt
            new_end = scheduled_for_dt + timedelta(seconds=duration)
            
            # Fetch all active (pending or running) jobs that have a scheduled time
            existing_jobs = db.scalars(
                select(SessionJob).where(
                    SessionJob.device_id == "observatory_pi_1",
                    SessionJob.status.in_(["pending", "running"]),
                    SessionJob.scheduled_for.isnot(None)
                )
            ).all()

            for job in existing_jobs:
                exist_start = job.scheduled_for
                exist_end = job.scheduled_for + timedelta(seconds=job.duration_seconds)
                
                # Check for time interval overlap: (StartA < EndB) and (EndA > StartB)
                if new_start < exist_end and new_end > exist_start:
                    return jsonify({
                        "error": f"Scheduling conflict: Overlaps with existing job #{job.id} "
                                 f"({exist_start.isoformat()} to {exist_end.isoformat()})"
                    }), 400

        new_job = SessionJob(
            device_id="observatory_pi_1",
            duration_seconds=duration,
            interval_seconds=interval,
            scheduled_for=scheduled_for_dt,
            status="pending"
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
                SessionJob.device_id == "observatory_pi_1",
                SessionJob.status == "pending",
                or_(
                    SessionJob.scheduled_for.is_(None),
                    SessionJob.scheduled_for <= now_utc
                )
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
                SessionJob.device_id == "observatory_pi_1",
                SessionJob.status == "pending",
                SessionJob.scheduled_for > now_utc
            )
            .order_by(SessionJob.scheduled_for.asc())
            .limit(1)
        )
        future_job = db.scalars(future_query).first()
        
        if future_job:
            # give pi timestamp for next job
            return jsonify({
                "status": "idle", 
                "next_scheduled_for": future_job.scheduled_for.isoformat()
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


@sessions_bp.post("/upload")
def upload_observing_session():
    """
    Receives the session .zip package and thumbnails from the Observatory Pi,
    saves them to data/thumbnails & data/sessions
    """
    session_id = request.form.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    session_file = request.files.get("sessions")
    thumbnail_files = request.files.getlist("thumbnails")

    if not session_file:
        return jsonify({"error": "No session zip file provided"}), 400

    # Save the session zip to backend/data/sessions/
    session_filename = f"session_{session_id}.zip"
    session_path = SESSIONS_DIR / session_filename
    session_file.save(session_path)

    # Save thumbnails to backend/data/thumbnails/
    thumbnail_map = {}
    for thumb in thumbnail_files:
        thumb_path = THUMBNAILS_DIR / thumb.filename
        thumb.save(thumb_path)
        orig_name = thumb.filename.replace("thumb_", "", 1)
        thumbnail_map[orig_name] = thumb.filename

    # Save to db
    with SessionLocal() as db:
        observing_session = db.get(ObservingSession, int(session_id))
        if not observing_session:
            observing_session = ObservingSession(
                id=int(session_id),
                night_of=date.today()
            )
            db.add(observing_session)
            db.flush()

        with zipfile.ZipFile(session_path, 'r') as zf:
            image_filenames = [name for name in zf.namelist() if name.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            for filename in image_filenames:
                thumb_filename = thumbnail_map.get(filename, f"thumb_{filename}")
              
                existing_img = db.scalar(
                    select(Image).where(
                        Image.session_id == observing_session.id,
                        Image.filename == filename
                    )
                )
                
                if not existing_img:
                    new_image = Image(
                        session_id=observing_session.id,
                        filename=filename,
                        file_path=filename,            
                        thumbnail_path=thumb_filename, 
                        captured_at=datetime.now(timezone.utc),
                        width=3840,
                        height=2160
                    )
                    db.add(new_image)

        db.commit()

    return jsonify({
        "status": "success",
        "message": f"Session {session_id} uploaded, saved, and registered successfully."
    }), 201