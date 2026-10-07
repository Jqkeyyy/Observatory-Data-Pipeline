from datetime import date, datetime

from sqlalchemy import BigInteger, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    __table_args__ = (Index("ix_image_metadata_gin", "metadata", postgresql_using="gin"),)

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
    meta: Mapped[dict | None] = mapped_column("metadata")  # "metadata" is reserved in SQLAlchemy
    ingested_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session: Mapped[ObservingSession] = relationship(back_populates="images")
    target: Mapped[Target | None] = relationship(back_populates="images")