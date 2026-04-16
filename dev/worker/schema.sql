CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    source_page TEXT,
    subscribed_at TEXT NOT NULL,
    ip_address TEXT
);
