import sqlite3

def test_init_db_creates_tables(tmp_path):
    from database import init_db, get_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = get_db()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    assert "conversations" in tables
    assert "leads" in tables
    assert "features" in tables
    assert "payments" in tables
    conn.close()

def test_init_db_enables_wal(tmp_path):
    from database import init_db, get_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = get_db()
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"
    conn.close()

def test_init_db_is_idempotent(tmp_path):
    from database import init_db, get_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    init_db(db_path)  # second call should not fail
    conn = get_db()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    assert "conversations" in tables
    conn.close()

def test_get_db_returns_connection(tmp_path):
    from database import init_db, get_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = get_db()
    assert conn is not None
    conn.execute("SELECT 1")
    conn.close()
