import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("")
print("=" * 50)
print("  SMART ATTENDANCE SYSTEM - DATABASE SETUP")
print("=" * 50)
print("")

# ================= USERS =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student','teacher','admin')),
    class_id INTEGER,
    rfid_uid TEXT,
    FOREIGN KEY(class_id) REFERENCES classes(id)
)
""")
print("[OK] users table ready")

# ================= CLASSES =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT NOT NULL,
    room_no TEXT
)
""")
print("[OK] classes table ready")

# ================= SUBJECTS =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL
)
""")
print("[OK] subjects table ready")

# ================= TIMETABLE =================
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
print("[OK] timetable table ready")

# ================= ATTENDANCE =================
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
print("[OK] attendance table ready")

# ================= LIVE ATTENDANCE (REAL-TIME TRACKING) =================
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
print("[OK] live_attendance table ready")

# ================= FACE LOGS (DURATION TRACKING) =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS face_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject_id INTEGER,
    duration REAL,
    date TEXT,
    FOREIGN KEY(student_id) REFERENCES users(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
)
""")
print("[OK] face_logs table ready")

# ================= RFID LOGS (ENTRY TRACKING) =================
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

# ================= RFID BUFFER (LIVE CARD REGISTRATION) =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS rfid_buffer (
    uid TEXT
)
""")
print("[OK] rfid_buffer table ready")

# ================= SCHEDULE (LEGACY SUPPORT) =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT,
    hour INTEGER,
    subject TEXT
)
""")
print("[OK] schedule table ready")

conn.commit()

# ================= CREATE ADMIN ACCOUNT =================
print("")
print("-" * 50)

try:
    cursor.execute("""
        INSERT INTO users (name, email, password, role)
        VALUES (?, ?, ?, ?)
    """, ("Admin", "admin@gmail.com", "admin", "admin"))
    conn.commit()
    print("[OK] Admin account created")
    print("     Email: admin@gmail.com")
    print("     Password: admin")
except sqlite3.IntegrityError:
    print("[!] Admin account already exists")

conn.close()

print("")
print("=" * 50)
print("  SETUP COMPLETE!")
print("=" * 50)
print("")
print("Next steps:")
print("1. Start Flask server:  cd backend && python app.py")
print("2. Start scheduler:     python auto_scheduler.py")
print("3. Start RFID service:  python rfid_service.py")
print("4. Open browser:        http://127.0.0.1:5000")
print("5. Login as admin and set up classes, subjects, users")
print("")
