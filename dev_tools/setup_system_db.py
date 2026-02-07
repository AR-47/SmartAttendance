"""
DATABASE SETUP - Smart Attendance System
=========================================
Run this FIRST to create all required tables.

Usage:
    cd dev_tools
    python setup_system_db.py
"""

import sqlite3
import os

# Connect to database in parent directory
db_path = os.path.join(os.path.dirname(__file__), "..", "database.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ================= USERS TABLE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student','teacher','admin')),
    class_id INTEGER,
    FOREIGN KEY(class_id) REFERENCES classes(id)
)
""")

# ================= CLASSES TABLE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT NOT NULL,
    room_no TEXT
)
""")

# ================= SUBJECTS TABLE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL
)
""")

# ================= TIMETABLE TABLE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER,
    subject_id INTEGER,
    teacher_id INTEGER,
    day TEXT,
    start_time TEXT,
    end_time TEXT,
    FOREIGN KEY(class_id) REFERENCES classes(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id),
    FOREIGN KEY(teacher_id) REFERENCES users(id)
)
""")

# ================= ATTENDANCE TABLE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject_id INTEGER,
    date TEXT,
    status TEXT CHECK(status IN ('Present','Absent')),
    FOREIGN KEY(student_id) REFERENCES users(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
)
""")

# ================= LIVE ATTENDANCE TABLE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS live_attendance (
    student_id TEXT PRIMARY KEY,
    name TEXT,
    face_entry TEXT,
    face_exit TEXT,
    duration REAL,
    status TEXT
)
""")

conn.commit()
conn.close()

print("[OK] Database tables created successfully!")
print("")
print("Tables created:")
print("  - users (with class_id)")
print("  - classes")
print("  - subjects")
print("  - timetable")
print("  - attendance")
print("  - live_attendance")
