"""Load the team's sample images so everyone has the same 50 pictures, times and IDs.

Run from backend\\ on an empty database:
    python scripts\\load_sample_images.py

The pictures live in backend\\sample_data\\images (committed to the repo).
Each file name holds its capture time and target:  2026-10-05_2030_Moon_<nasa id>.jpg

One time only (Jake), to build that folder from the NASA images already in your database:
    python scripts\\load_sample_images.py --create
"""

import argparse
import shutil
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))  # so "from db..." works

from sqlalchemy import func, select  # noqa: E402

from db.models import Image, ObservingSession, Target  # noqa: E402
from db.session import SessionLocal  # noqa: E402

SAMPLE_DIR = BACKEND / "sample_data" / "images"
DATA_DIR = BACKEND / "data"
TZ = ZoneInfo("America/Chicago")
TYPES = {"Moon": "moon", "Jupiter": "planet", "Saturn": "planet", "Mars": "planet", "Orion Nebula": "deep sky"}

# Fixed schedule for --create: 10 pictures a night, every 35 minutes from 8:30pm
FIRST_NIGHT = date(2026, 10, 5)
PER_NIGHT = 10
GAP = timedelta(minutes=35)

RESET_STEPS = """
Your database already has other images, so IDs won't match the team's.
Wipe it and reload (deletes everything in your local database):
    python scripts\\setup_db.py --reset
"""


def create():
    """Copy every image in the database into sample_data with a fixed time in its name."""
    if SAMPLE_DIR.exists() and any(SAMPLE_DIR.iterdir()):
        sys.exit(f"{SAMPLE_DIR} already has files. Empty it first if you want to rebuild it.")
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        images = db.scalars(select(Image).order_by(Image.id)).all()
        missing = [img for img in images if not (DATA_DIR / img.file_path).exists()]
        if missing:
            print(f"Skipping {len(missing)} images whose files aren't in {DATA_DIR / 'images'}")
        images = [img for img in images if img not in missing]
        # Take turns between targets so each night has a mix: Moon, Jupiter, Saturn, ...
        by_target = {}
        for img in images:
            by_target.setdefault(img.target.name if img.target else "Unknown", []).append(img)
        mixed = []
        while any(by_target.values()):
            for group in by_target.values():
                if group:
                    mixed.append(group.pop(0))

        for i, img in enumerate(mixed):
            night, slot = divmod(i, PER_NIGHT)
            captured = datetime.combine(FIRST_NIGHT + timedelta(days=night), time(20, 30), TZ) + slot * GAP
            target = (img.target.name if img.target else "Unknown").replace(" ", "-")
            nasa_id = (img.meta or {}).get("nasa_id") or Path(img.file_path).stem
            name = f"{captured:%Y-%m-%d_%H%M}_{target}_{nasa_id}.jpg"
            shutil.copy2(DATA_DIR / img.file_path, SAMPLE_DIR / name)

    total_mb = sum(f.stat().st_size for f in SAMPLE_DIR.iterdir()) / 1_000_000
    print(f"Wrote {len(mixed)} images ({total_mb:.0f} MB) to {SAMPLE_DIR}")


def load():
    """Add every sample image to the database, oldest first, so IDs match on every computer."""
    files = sorted(SAMPLE_DIR.glob("*.jpg"))  # names start with the time, so this is time order
    if not files:
        sys.exit(f"No images in {SAMPLE_DIR}. Pull the latest main first.")
    (DATA_DIR / "images").mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        sample_paths = {f"images/{f.name}" for f in files}
        existing = set(db.scalars(select(Image.file_path)))
        if existing - sample_paths:
            sys.exit(RESET_STEPS)

        added = 0
        for f in files:
            file_path = f"images/{f.name}"
            if file_path in existing:
                if not (DATA_DIR / file_path).exists():
                    shutil.copy2(f, DATA_DIR / file_path)  # already loaded, but put back a missing file
                continue
            day, hhmm, target_name, nasa_id = f.stem.split("_", 3)
            captured = datetime.strptime(f"{day} {hhmm}", "%Y-%m-%d %H%M").replace(tzinfo=TZ)
            night = (captured - timedelta(hours=12)).date()  # after-midnight shots count as the night before
            target_name = target_name.replace("-", " ")

            shutil.copy2(f, DATA_DIR / file_path)
            target = db.scalar(select(Target).where(Target.name == target_name))
            session = db.scalar(select(ObservingSession).where(ObservingSession.night_of == night))
            db.add(Image(
                session=session or ObservingSession(night_of=night),
                target=target or Target(name=target_name, type=TYPES.get(target_name)),
                file_path=file_path,
                captured_at=captured,
                width=3840,  # every sample frame is 4K
                height=2160,
                file_size_bytes=f.stat().st_size,
                meta={"source": "sample", "nasa_id": nasa_id},
            ))
            db.commit()
            added += 1

        total = db.scalar(select(func.count(Image.id)))
    print(f"Added {added} images ({total} total).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true", help="one time: build sample_data from your database")
    create() if parser.parse_args().create else load()
