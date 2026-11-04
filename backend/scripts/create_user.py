"""Create an account, or update one that already exists.

Run from backend\\:
    python scripts\\create_user.py student@uww.edu "Student Name"           student (role "user")
    python scripts\\create_user.py nine@uww.edu "Dr. Nine" --admin          admin
It asks for the password, so it never ends up in your terminal history.
"""

import argparse
import getpass
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))  # so "from db..." works

from sqlalchemy import select  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402  (comes with Flask)

from db.models import User  # noqa: E402
from db.session import SessionLocal  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Create an account, or update one that already exists.")
    parser.add_argument("email")
    parser.add_argument("name")
    parser.add_argument("--admin", action="store_true", help="make this account an admin")
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    if len(password) < 8:
        sys.exit("Password must be at least 8 characters.")
    if getpass.getpass("Again: ") != password:
        sys.exit("Passwords don't match.")

    email = args.email.strip().lower()
    role = "admin" if args.admin else "user"
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email)
            db.add(user)
        user.name = args.name
        user.role = role
        user.password_hash = generate_password_hash(password)
        db.commit()
    print(f"Saved {email} as {role}.")


if __name__ == "__main__":
    main()
