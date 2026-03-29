"""SQLite database connection and schema management."""

import sqlite3
import logging

logger = logging.getLogger("service_bot")

_db_path: str = ""

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id TEXT NOT NULL,
    responses TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS features (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT UNIQUE NOT NULL,
    session_id TEXT,
    service_id TEXT,
    amount INTEGER NOT NULL,
    currency TEXT DEFAULT 'ZAR',
    email TEXT,
    status TEXT DEFAULT 'pending',
    payment_url TEXT,
    paystack_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_payments_reference ON payments(reference);
CREATE INDEX IF NOT EXISTS idx_payments_session ON payments(session_id);

CREATE TABLE IF NOT EXISTS runtime_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def init_db(path: str) -> None:
    """Initialize the database: create tables and enable WAL mode."""
    global _db_path
    _db_path = path
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", path)


def get_db() -> sqlite3.Connection:
    """Get a new database connection."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    return conn
