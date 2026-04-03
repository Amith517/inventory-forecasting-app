import sqlite3
from pathlib import Path

DB_PATH = Path("data/inventory.db")

def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        category TEXT,
        min_stock INTEGER,
        early_warning_stock INTEGER,
        price REAL,
        is_essential INTEGER DEFAULT 0
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        product_id INTEGER PRIMARY KEY,
        current_stock INTEGER DEFAULT 0,
        last_updated TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        sale_qty INTEGER,
        sale_date TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        alert_type TEXT,
        message TEXT,
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS essential_products (
        product_id INTEGER PRIMARY KEY
    );
    """)

    conn.commit()
    conn.close()

init_db()