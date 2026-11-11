"""Booking capture sessions. Used by the API, and later by the Pi's capture script:
    session = active_session(db)                     # None means don't take pictures
    interval = db.get(CaptureSettings, 1).interval_s  # seconds between pictures
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db.models import CaptureSession

TZ = ZoneInfo("America/Chicago")  # observatory time


class SessionConflict(Exception):
    """The new session overlaps one that's already booked. .session is the one in the way."""

    def __init__(self, message, session):
        super().__init__(message)
        self.session = session


def now():
    return datetime.now(timezone.utc)


def parse_time(value):
    """'2026-11-03T21:00' -> datetime. Times without a timezone are observatory time."""
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=TZ)


def active_session(db, at=None):
    """The session happening right now, or None."""
    at = at or now()
    return db.scalar(select(CaptureSession).where(CaptureSession.start_at <= at, CaptureSession.end_at > at))


def overlapping_session(db, start_at, end_at):
    """The earliest booked session that overlaps these times, or None. Back-to-back is fine."""
    return db.scalar(
        select(CaptureSession)
        .where(CaptureSession.start_at < end_at, CaptureSession.end_at > start_at)
        .order_by(CaptureSession.start_at)
        .limit(1)
    )


def clock(dt):
    """'9:00 PM' in observatory time."""
    return dt.astimezone(TZ).strftime("%I:%M %p").lstrip("0")


def conflict_message(session):
    if session.start_at <= now() < session.end_at:
        return f"There's an active session until {clock(session.end_at)}."
    day = session.start_at.astimezone(TZ)
    return f"That overlaps a session on {day:%a %b} {day.day} from {clock(session.start_at)} to {clock(session.end_at)}."


def book_session(db, end_at, start_at=None, created_by=None):
    """Book a session that starts now, or at start_at.
    Raises ValueError for bad times and SessionConflict if another session is in the way."""
    start_at = start_at or now()
    if end_at <= start_at:
        raise ValueError("End time must be after the start time.")
    if start_at < now() - timedelta(minutes=1):
        raise ValueError("Start time is in the past.")

    if existing := overlapping_session(db, start_at, end_at):
        raise SessionConflict(conflict_message(existing), existing)

    booked = CaptureSession(start_at=start_at, end_at=end_at, created_by=created_by)
    db.add(booked)
    try:
        db.commit()
    except IntegrityError:  # someone else booked that time a split second earlier
        db.rollback()
        if existing := overlapping_session(db, start_at, end_at):
            raise SessionConflict(conflict_message(existing), existing) from None
        raise
    return booked
