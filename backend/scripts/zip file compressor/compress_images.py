import argparse
import zipfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
IMAGES_DIR = BACKEND / "data" / "images"
ZIP_PATH = BACKEND / "data" / "images.zip"


def compress_images():
    if not IMAGES_DIR.exists():
        print(f"Image directory not found: {IMAGES_DIR}")
        return

    images = [
        path
        for path in IMAGES_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in (".jpg", ".jpeg")
    ]

    if not images:
        print("No JPEG images found.")
        return

    original_size = sum(path.stat().st_size for path in images)

    with zipfile.ZipFile(
        ZIP_PATH,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for image in images:
            archive.write(image, arcname=image.name)
            print(f"Added: {image.name}")

    compressed_size = ZIP_PATH.stat().st_size

    print("\nCompression complete!")
    print(f"Images processed: {len(images)}")
    print(f"Original size: {original_size / (1024 * 1024):.2f} MB")
    print(f"ZIP size: {compressed_size / (1024 * 1024):.2f} MB")

    if original_size > 0:
        saved = (1 - compressed_size / original_size) * 100
        print(f"Size reduction: {saved:.2f}%")
    print(f"ZIP saved to: {ZIP_PATH}")


if __name__ == "__main__":
    compress_images()
