"""Download NASA test images as 4K frames and add them to the database.

Run from backend\\:  python scripts\\load_test_images.py --count 5   (images per target)
Needs: pip install pillow
"""

import argparse
import io
import json
import random
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image as PILImage

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))  # so "from db..." works

from sqlalchemy import select  # noqa: E402

from db.models import Image, ObservingSession, Target  # noqa: E402
from db.session import SessionLocal  # noqa: E402

DATA_DIR = BACKEND / "data"
TZ = ZoneInfo("America/Chicago")

# name, type, NASA search words, size in the 4K frame (fraction of its height)
TARGETS = [
    ("Moon", "moon", "full moon", 0.85),
    ("Jupiter", "planet", "jupiter juno", 0.25),
    ("Saturn", "planet", "saturn cassini", 0.30),
    ("Mars", "planet", "mars hubble", 0.12),
    ("Orion Nebula", "deep sky", "orion nebula", 0.90),
]


def get(url):
    request = urllib.request.Request(url.replace("http://", "https://"), headers={"User-Agent": "observatory-test"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def nasa_images(query, count):
    """Yield (nasa_id, image bytes) for the first `count` photos NASA finds."""
    params = urllib.parse.urlencode({"q": query, "media_type": "image", "page_size": 100})
    for item in json.loads(get(f"https://images-api.nasa.gov/search?{params}"))["collection"]["items"]:
        if count == 0:
            return
        try:
            files = json.loads(get(item["href"]))  # every size NASA has for this image
            jpgs = sorted((f for f in files if f.lower().endswith(("~large.jpg", "~orig.jpg"))), key=lambda f: "~orig" in f)
            if jpgs:
                yield item["data"][0]["nasa_id"], get(jpgs[0])  # large if there is one
                count -= 1
        except Exception:
            continue  # skip any image that fails to download


def to_4k(data, size):
    """Resize the picture and center it in a black 3840x2160 frame, like a webcam on a telescope."""
    obj = PILImage.open(io.BytesIO(data)).convert("RGB")
    scale = 2160 * size / max(obj.size)
    obj = obj.resize((round(obj.width * scale), round(obj.height * scale)))
    frame = PILImage.new("RGB", (3840, 2160))
    frame.paste(obj, ((3840 - obj.width) // 2, (2160 - obj.height) // 2))
    return frame


def main(count):
    (DATA_DIR / "images").mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        for name, kind, query, size in TARGETS:
            target = db.scalar(select(Target).where(Target.name == name)) or Target(name=name, type=kind)
            for i, (nasa_id, data) in enumerate(nasa_images(query, count)):
                file_path = f"images/{nasa_id}.jpg"
                if db.scalar(select(Image.id).where(Image.file_path == file_path)):
                    continue  # already loaded
                to_4k(data, size).save(DATA_DIR / file_path, quality=92)

                # Fake capture time: 8:30pm-3:30am, spread over the last 3 nights
                evening = datetime.combine(date.today() - timedelta(days=i % 3 + 1), time(20, 30), TZ)
                captured = evening + timedelta(minutes=random.randint(0, 420))
                night = (captured - timedelta(hours=12)).date()
                session = db.scalar(select(ObservingSession).where(ObservingSession.night_of == night))

                db.add(Image(
                    session=session or ObservingSession(night_of=night),
                    target=target,
                    file_path=file_path,
                    captured_at=captured,
                    width=3840,
                    height=2160,
                    meta={"source": "nasa-test", "nasa_id": nasa_id},
                ))
            db.commit()
            print(f"{name}: done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5, help="images per target (default: 5)")
    main(parser.parse_args().count)
