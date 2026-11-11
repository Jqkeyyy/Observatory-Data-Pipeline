from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY, ExcludeConstraint

from db.base import Base


class ObservingSession(Base):
    __tablename__ = "observing_session"

    id: Mapped[int] = mapped_column(primary_key=True)
    night_of: Mapped[date] = mapped_column(unique=True)
    started_at: Mapped[datetime | None]
    ended_at: Mapped[datetime | None]
    notes: Mapped[str | None]

    images: Mapped[list["Image"]] = relationship(back_populates="session")


class Target(Base):
    __tablename__ = "target"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    type: Mapped[str | None]

    images: Mapped[list["Image"]] = relationship(back_populates="target")


class Image(Base):
    __tablename__ = "image"
    __table_args__ = (
        Index("ix_image_metadata_gin", "metadata", postgresql_using="gin"),
        Index("ix_image_tags_gin", "tags", postgresql_using="gin"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("observing_session.id"), index=True)
    target_id: Mapped[int | None] = mapped_column(ForeignKey("target.id", ondelete="SET NULL"), index=True)
    file_path: Mapped[str] = mapped_column(unique=True)
    preview_path: Mapped[str | None]
    captured_at: Mapped[datetime] = mapped_column(index=True)
    exposure_s: Mapped[float | None]
    width: Mapped[int | None]
    height: Mapped[int | None]
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    sharpness: Mapped[float | None] = mapped_column(index=True)
    meta: Mapped[dict | None] = mapped_column("metadata") 
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, server_default="{}")
    ingested_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session: Mapped[ObservingSession] = relationship(back_populates="images")
    target: Mapped[Target | None] = relationship(back_populates="images")


class User(Base):
    """role "user" = student: can tag images and book capture sessions.
    role "admin" = professor: can also change the capture interval, edit or end any session, and manage users."""

    __tablename__ = "users"  # "user" is a reserved word in Postgres
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    password_hash: Mapped[str]
    role: Mapped[str] = mapped_column(default="user", server_default="user")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class CaptureSession(Base):
    """A time window when the Pi takes pictures. Anyone logged in can book one.
    Not the same as ObservingSession, which groups the finished pictures by night."""

    __tablename__ = "capture_session"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="ck_capture_session_end_after_start"),
        # Postgres itself refuses two sessions whose times overlap, even if two people click at once
        ExcludeConstraint(
            (text("tstzrange(start_at, end_at)"), "&&"),
            name="ex_capture_session_no_overlap",
            using="gist",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    start_at: Mapped[datetime] = mapped_column(index=True)
    end_at: Mapped[datetime]
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    created_by_user: Mapped[User | None] = relationship()


class CaptureSettings(Base):
    """Always exactly one row (id = 1). Admins change it; the capture script reads it."""

    __tablename__ = "capture_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_capture_settings_one_row"),
        CheckConstraint("interval_s >= 30", name="ck_capture_settings_interval"),  # Dr. Nine: max ~2 per minute
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False, default=1)
    interval_s: Mapped[int] = mapped_column(server_default="60")  # seconds between pictures
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    updated_by_user: Mapped[User | None] = relationship()