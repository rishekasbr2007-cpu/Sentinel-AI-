"""
SentinelAI - Database setup
Creates the SQLite database with tables for users, alerts, and reports.
No external DB server needed - SQLite is a single local file (100% free).
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "sentinelai.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'Security Analyst',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_ref TEXT,
            risk_score REAL,
            risk_level TEXT,
            explanation TEXT,
            quantum_flag INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            analyst_feedback TEXT
        )
    """)
    try:
        cur.execute("ALTER TABLE alerts ADD COLUMN analyst_feedback TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists

    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT,
            success INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Default admin account so you can log in immediately: admin@sentinelai.com / Admin@123
    cur.execute("SELECT * FROM users WHERE email = ?", ("admin@sentinelai.com",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@sentinelai.com", generate_password_hash("Admin@123"), "Admin"),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
    print("Default login -> email: admin@sentinelai.com | password: Admin@123")
