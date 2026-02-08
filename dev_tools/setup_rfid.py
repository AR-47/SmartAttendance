"""
RFID SETUP - Smart Attendance System
=====================================
This script adds RFID support to the database:
1. Adds rfid_uid column to users table
2. Creates rfid_logs table for tracking card taps

Run once:
    cd dev_tools
    python setup_rfid.py
"""

import sqlite3
import os

# Connect to database in parent directory
db_path = os.path.join(os.path.dirname(__file__), "..", "database.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ================= ADD RFID COLUMN TO USERS =================
try:
    cursor.execute("ALTER TABLE users ADD COLUMN rfid_uid TEXT")
    print("[OK] Added rfid_uid column to users table")
except sqlite3.OperationalError:
    print("[!] rfid_uid column already exists")

# ================= CREATE RFID LOGS TABLE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS rfid_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject_id INTEGER,
    timestamp TEXT,
    FOREIGN KEY(student_id) REFERENCES users(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
)
""")
print("[OK] rfid_logs table ready")

conn.commit()
conn.close()

print("")
print("=" * 50)
print("RFID setup complete!")
print("")
print("Next steps:")
print("1. Tap each student's card in Notepad to get UID")
print("2. Update each student's rfid_uid in the database")
print("3. Run rfid_reader.py during classes")
print("=" * 50)
