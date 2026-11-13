CREATE TABLE IF NOT EXISTS spools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    material TEXT NOT NULL,
    color TEXT NOT NULL,
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