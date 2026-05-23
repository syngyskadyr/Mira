"""SQLite3 database helper for Mira loop bot.

This module provides a single `get_connection()` function which returns a
`sqlite3.Connection` to the project's database file `mira_loop.db` and a
`create_tables()` helper that ensures the schema exists. `create_tables()` is
called on import so the database is ready to use.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Optional

DB_FILENAME = "mira_loop.db"


def _db_path() -> str:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(root, DB_FILENAME)


def get_connection() -> sqlite3.Connection:
    """Return a sqlite3.Connection to the project's database file.

    The returned connection has foreign key support enabled.
    """
    path = _db_path()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables(conn: Optional[sqlite3.Connection] = None) -> None:
    """Create required tables if they do not exist.

    If `conn` is not provided, a new connection will be opened and closed.
    """
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        segment TEXT,
        xp INTEGER DEFAULT 0,
        referral_code TEXT UNIQUE,
        referrer_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(referrer_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        segment TEXT,
        text TEXT,
        proof_type TEXT,
        xp_reward INTEGER DEFAULT 50
    );

    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_id INTEGER,
        proof_type TEXT,
        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(task_id) REFERENCES tasks(id)
    );

    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        xp_awarded INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(referrer_id) REFERENCES users(id),
        FOREIGN KEY(referred_id) REFERENCES users(id)
    );
    """)
    conn.commit()

    if own_conn:
        conn.close()


# Ensure schema exists on import
create_tables()


__all__ = ["get_connection", "create_tables"]
