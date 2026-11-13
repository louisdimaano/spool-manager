import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "spools.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema = (BASE_DIR / "schema.sql").read_text()
    conn = get_db()
    conn.executescript(schema)
    conn.close()