import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "spools.db"))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


NEW_COLUMNS = {
    "color_hex": "TEXT",
    "color_hex_2": "TEXT",
    "color_hex_3": "TEXT",
    "color_style": "TEXT NOT NULL DEFAULT 'split'",
    "is_translucent": "INTEGER NOT NULL DEFAULT 0",
    "finish": "TEXT NOT NULL DEFAULT 'Basic'",
}


def init_db():
    schema = (BASE_DIR / "schema.sql").read_text()
    conn = get_db()
    conn.executescript(schema)

    existing = [row["name"] for row in conn.execute("PRAGMA table_info(spools)")]
    for name, column_type in NEW_COLUMNS.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE spools ADD COLUMN {name} {column_type}")

    conn.commit()
    conn.close()