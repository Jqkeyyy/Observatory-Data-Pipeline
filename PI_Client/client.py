"""Runs on the Observatory Pi (see README.md for running it as a service).
Asks the server for a job, takes the pictures, then uploads them as one zip plus thumbnails.
"""

import os
import shutil
import time
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image

from scripts.compress import package_session

SERVER_URL = os.environ.get("OBSERVATORY_SERVER", "http://192.168.1.50:5000")
JOBS_URL = f"{SERVER_URL}/api/sessions/jobs"
DEVICE_ID = "observatory_pi_1"
IDLE_POLL_SECONDS = 60

LOCAL_STAGING_DIR = Path(os.environ.get("OBSERVATORY_STAGING", "/home/pi/observatory_staging")) / "current_session"


def capture_photos(duration, interval):
    """Simulates or executes camera capture, saving raw frames locally."""
    shutil.rmtree(LOCAL_STAGING_DIR, ignore_errors=True)  # leftovers from a failed job
    LOCAL_STAGING_DIR.mkdir(parents=True)

    print(f"Starting session capture: duration={duration}s, interval={interval}s")

    start_time = time.time()
    frame_count = 0
    while time.time() - start_time < duration:
        frame_count += 1
        # The server reads the capture time from this name: frame_<unix time>_<n>.jpg
        frame_path = LOCAL_STAGING_DIR / f"frame_{int(time.time())}_{frame_count:03d}.jpg"

        # --- CAMERA CAPTURE GOES HERE ---
        mock_img = Image.new("RGB", (3840, 2160), color=(20, 20, 40))
        mock_img.save(frame_path, "JPEG")
        # ---------------------------------

        print(f"Captured frame {frame_count} -> {frame_path.name}")
        time.sleep(max(0, min(interval, duration - (time.time() - start_time))))

    print("Session capture completed.")
    return frame_count


def acknowledge(job_id, status):
    """Tell the server the job is 'running', 'completed', or 'error'."""
    try:
        requests.post(f"{JOBS_URL}/{job_id}/ack", json={"status": status}, timeout=10).raise_for_status()
    except requests.RequestException as e:
        print(f"Couldn't mark job {job_id} as {status}: {e}")


def upload_session(job_id, zip_path, thumbnail_files):
    """Handles the actual network POST request to upload files to the server."""
    with ExitStack() as stack:
        files = [("archive", (zip_path.name, stack.enter_context(open(zip_path, "rb")), "application/zip"))]
        for t_path in thumbnail_files:
            files.append(("thumbnails", (t_path.name, stack.enter_context(open(t_path, "rb")), "image/jpeg")))

        try:
            print(f"Uploading job {job_id} package to server...")
            response = requests.post(f"{JOBS_URL}/upload", data={"job_id": job_id}, files=files, timeout=300)
        except requests.exceptions.RequestException as e:
            print(f"Network error during upload: {e}")
            return False

    if response.status_code == 201:
        print("Session successfully uploaded and registered!")
        return True
    print(f"Server rejected upload: {response.status_code} - {response.text}")
    return False


def execute_imaging_session(job):
    """Run one job from start to finish and report how it went."""
    job_id = job["id"]
    print(f"Starting job {job_id}...")
    acknowledge(job_id, "running")

    try:
        capture_photos(job["duration_seconds"], job["interval_seconds"])
        zip_path, thumbnail_files = package_session(job_id, LOCAL_STAGING_DIR)
        uploaded = upload_session(job_id, zip_path, thumbnail_files)
    except Exception as e:  # camera or disk trouble: report it instead of crashing the service
        print(f"Job {job_id} failed: {e}")
        uploaded = False

    acknowledge(job_id, "completed" if uploaded else "error")
    if uploaded:
        shutil.rmtree(LOCAL_STAGING_DIR, ignore_errors=True)
        zip_path.unlink(missing_ok=True)
    # If it failed, the pictures stay in the staging folder until the next job starts


def main():
    print(f"Raspberry Pi worker started. Polling server at {SERVER_URL}...")

    while True:
        sleep_time = IDLE_POLL_SECONDS
        try:
            response = requests.get(f"{JOBS_URL}/next-pending", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "idle" and "id" in data:
                execute_imaging_session(data)
                continue

            next_scheduled_str = data.get("next_scheduled_for")
            if next_scheduled_str:
                next_dt = datetime.fromisoformat(next_scheduled_str.replace("Z", "+00:00"))
                seconds_until_job = (next_dt - datetime.now(timezone.utc)).total_seconds()
                sleep_time = max(1, min(seconds_until_job, IDLE_POLL_SECONDS))
                print(f"Next job in {int(seconds_until_job)}s. Sleeping for {int(sleep_time)}s...")

        except (requests.RequestException, ValueError) as e:
            print(f"Polling error: {e}")

        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
