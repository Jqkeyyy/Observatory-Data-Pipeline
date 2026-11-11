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

class SessionJob(Base):
    __tablename__ = "session_job"
    __table_args__ = (
        Index("ix_session_job_pending", "device_id", "created_at", postgresql_where=(func.lower("status") == "pending")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(index=True)
    duration_seconds: Mapped[int]
    interval_seconds: Mapped[int]
    scheduled_for: Mapped[datetime | None] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(default="pending", server_default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_id": self.device_id,
            "duration_seconds": self.duration_seconds,
            "interval_seconds": self.interval_seconds,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


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
