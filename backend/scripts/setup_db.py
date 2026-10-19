"""Set up your local database with the team's sample images in one command.

Open Docker Desktop and activate the venv, then from backend\\:
    python scripts\\setup_db.py           start Postgres, create the tables, load the sample images
    python scripts\\setup_db.py --reset   same, but wipe your local database first

Safe to run again; it only adds what's missing.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
DB_DIR = BACKEND / "db"
ENV_FILE = BACKEND / ".env"
DEFAULT_URL = "postgresql+psycopg://observatory:observatory@localhost:5433/observatory"
DOCKER_HELP = "Docker isn't running. Open Docker Desktop, wait for it to finish starting, then run this again."


def run(cmd, cwd, error):
    try:
        ok = subprocess.run(cmd, cwd=cwd).returncode == 0
    except FileNotFoundError:
        ok = False
        error = f"Couldn't find '{cmd[0]}'. Is it installed?"
    if not ok:
        sys.exit(error)


def wait_for_postgres():
    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["DATABASE_URL"])
    for _ in range(30):  # the first start takes a few seconds
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine.dispose()
        except Exception as e:
            last_error = e
            time.sleep(1)
    sys.exit(f"Couldn't connect to Postgres after 30 seconds:\n{last_error}")


def main(reset):
    if not ENV_FILE.exists():
        ENV_FILE.write_text(f"DATABASE_URL={DEFAULT_URL}\n")
        print("Created backend\\.env")
    load_dotenv(ENV_FILE)

    if reset:
        print("Wiping your local database...")
        run(["docker", "compose", "down", "-v"], DB_DIR, DOCKER_HELP)
    print("Starting Postgres...")
    run(["docker", "compose", "up", "-d", "db"], DB_DIR, DOCKER_HELP)
    wait_for_postgres()

    print("Creating tables...")
    run([sys.executable, "-m", "alembic", "upgrade", "head"], BACKEND, "Creating the tables failed (see the error above).")

    print("Loading sample images...")
    sys.path.insert(0, str(Path(__file__).parent))
    from load_sample_images import load

    load()
    print("Done. Start the API with:  python server.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="wipe your local database first")
    main(parser.parse_args().reset)
