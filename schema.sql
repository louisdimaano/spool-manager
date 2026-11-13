CREATE TABLE IF NOT EXISTS spools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    material TEXT NOT NULL,
    finish TEXT NOT NULL DEFAULT 'Basic',
    color TEXT NOT NULL,
    color_hex TEXT,
    color_hex_2 TEXT,
    color_hex_3 TEXT,
    color_style TEXT NOT NULL DEFAULT 'split',
    is_translucent INTEGER NOT NULL DEFAULT 0,
    total_g INTEGER NOT NULL DEFAULT 1000,
    remaining_g INTEGER NOT NULL,
    empty_spool_g INTEGER,
    cost REAL,
    cfs_slot TEXT,
    in_dry_box INTEGER NOT NULL DEFAULT 0,
    opened_on TEXT,
    backup_brand TEXT,
    backup_link TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS prints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spool_id INTEGER NOT NULL REFERENCES spools(id) ON DELETE CASCADE,
    grams_used INTEGER NOT NULL,
    printed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);