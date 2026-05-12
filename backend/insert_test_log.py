import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "project.db")

print("Using DB at:", DB_PATH)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
INSERT INTO logs (username, action, page)
VALUES (?, ?, ?)
""", (
    "system",
    "TEST_ALERT",
    "dashboard"
))

conn.commit()
conn.close()

print("Log inserted successfully.")