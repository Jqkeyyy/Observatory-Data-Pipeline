<!-- In VS Code, press Ctrl+Shift+V -->
# Database

PostgreSQL in Docker. It stores **information about** each image (when, what target, where the file is). The image files themselves live on disk.

## For API developers

### Setup on your computer (Windows PowerShell)

Open Docker Desktop first.

```powershell
# From backend\db: start Postgres
docker compose up -d db

# From the repo root: Python environment
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements-db.txt

# From backend\: settings file, then create the tables
Set-Content .env "DATABASE_URL=postgresql+psycopg://observatory:observatory@localhost:5433/observatory"
python -m alembic upgrade head
```

Check: `docker exec observatory-db psql -U observatory -c "\dt"` should list the three tables.

### Using the database

Import from `db.models` and `db.session`. Run your code from `backend\` so those imports work.

```python
from sqlalchemy import select
from db.models import Image, Target
from db.session import SessionLocal

with SessionLocal() as db:
    # Read: 10 newest images
    images = db.scalars(select(Image).order_by(Image.captured_at.desc()).limit(10)).all()

    # Write: add a target
    db.add(Target(name="Mars", type="planet"))
    db.commit()
```

### Connecting from Flask

Needs `pip install flask flask-cors`.

```python
from flask import Flask
from flask_cors import CORS
from db.models import Image
from db.session import SessionLocal

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])  # React dev server
```

### Good to know

- In `models.py`, `| None` means the column can be empty.
- The `metadata` column is `image.meta` in Python (SQLAlchemy reserves the name).
- Times are stored in UTC. Convert to Central time when displaying.
- `image.session` and `image.target` give you the related row, no join needed.
- Don't change tables yourself. Ask Jake.
- After pulling new changes, run `python -m alembic upgrade head` from `backend\`.

## Running the server

In Progress

## Common problems

| Error | Fix |
|---|---|
| `failed to connect to the docker API` | Open Docker Desktop |
| `alembic is not recognized` | Use `python -m alembic` |
| `running scripts is disabled` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `No module named 'db'` | Run from `backend\` |

Reset to an empty database: `docker compose down -v` in `backend\db`, then redo setup. **This deletes all data.**