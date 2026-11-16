""" Generate image thumbnails and compress a finished job locally on the Pi """

import zipfile
from pathlib import Path

from PIL import Image

THUMB_SIZE = (960, 540)


def package_session(job_id: int, local_session_dir: Path):
    """Zip every picture in local_session_dir and make a 960x540 thumbnail of each.
    Returns (zip path, [thumbnail paths]). Thumbnails are named thumb_<picture name>,
    which is how the server matches them to their pictures."""
    thumbnails_dir = local_session_dir / "thumbnails"
    thumbnails_dir.mkdir(exist_ok=True)

    zip_path = local_session_dir.parent / f"job_{job_id}.zip"
    thumbnail_files = []

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for img_path in sorted(local_session_dir.glob("*.jpg")):
            zf.write(img_path, arcname=img_path.name)

            with Image.open(img_path) as img:
                img.thumbnail(THUMB_SIZE)  # keeps the shape of the picture, unlike resize()
                thumb_path = thumbnails_dir / f"thumb_{img_path.name}"
                img.save(thumb_path, "JPEG", quality=85)
                thumbnail_files.append(thumb_path)

    return zip_path, thumbnail_files
