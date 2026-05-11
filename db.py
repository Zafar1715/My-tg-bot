import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("nakladnye.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        driver TEXT,
        car_number TEXT,
        tons REAL,
        invoice_number TEXT,
        object_name TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        time TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_invoice(data):
    conn = sqlite3.connect("nakladnye.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO invoices (date, driver, car_number, tons, invoice_number, object_name)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["date"],
        data["driver"],
        data["car"],
        data["tons"],
        data["invoice"],
        data["object"]
    ))

    conn.commit()
    conn.close()


def get_report():
    conn = sqlite3.connect("nakladnye.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT object_name, SUM(tons)
        FROM invoices
        GROUP BY object_name
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def log_action(user_id, action):
    conn = sqlite3.connect("nakladnye.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO logs (user_id, action, time)
        VALUES (?, ?, ?)
    """, (user_id, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()