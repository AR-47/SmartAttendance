"""
FINALIZE ATTENDANCE - Smart Attendance System
==============================================
This script merges RFID and Face data to produce final attendance.

Logic:
    Present = RFID tap (entry verified) + Face duration >= MIN_DURATION
    Absent = Missing RFID OR insufficient face time

Called automatically after each class session ends.

Can also run manually:
    python finalize_attendance.py
"""

import sqlite3
import os
from datetime import datetime

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
MIN_DURATION = 30  # Minimum minutes required for "Present" status

def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def finalize_attendance(subject_id=None):
    """Merge RFID + Face data and update attendance table"""
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    log("=" * 50)
    log("FINALIZING ATTENDANCE")
    log(f"Date: {today}")
    log(f"Minimum duration: {MIN_DURATION} minutes")
    log("=" * 50)
    
    # Get students who tapped RFID today
    if subject_id:
        cursor.execute("""
            SELECT DISTINCT student_id FROM rfid_logs
            WHERE DATE(timestamp) = ? AND subject_id = ?
        """, (today, subject_id))
    else:
        cursor.execute("""
            SELECT DISTINCT student_id FROM rfid_logs
            WHERE DATE(timestamp) = ?
        """, (today,))
    
    rfid_students = {row["student_id"] for row in cursor.fetchall()}
    log(f"RFID entries found: {len(rfid_students)} students")
    
    # Get face duration data
    if subject_id:
        cursor.execute("""
            SELECT student_id, subject_id, duration FROM face_logs
            WHERE date = ? AND subject_id = ?
        """, (today, subject_id))
    else:
        cursor.execute("""
            SELECT student_id, subject_id, duration FROM face_logs
            WHERE date = ?
        """, (today,))
    
    face_data = cursor.fetchall()
    log(f"Face records found: {len(face_data)} entries")
    
    # Process each face record
    present_count = 0
    absent_count = 0
    
    for row in face_data:
        student_id = row["student_id"]
        subj_id = row["subject_id"]
        duration = row["duration"] or 0
        
        # Get student name for logging
        cursor.execute("SELECT name FROM users WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        student_name = student["name"] if student else f"ID:{student_id}"
        
        # Determine status
        rfid_verified = student_id in rfid_students
        duration_ok = duration >= MIN_DURATION
        
        if rfid_verified and duration_ok:
            status = "Present"
            present_count += 1
            log(f"  [OK] {student_name}: RFID ✓ + Face {duration:.1f}min ✓ → PRESENT")
        else:
            status = "Absent"
            absent_count += 1
            reason = []
            if not rfid_verified:
                reason.append("No RFID")
            if not duration_ok:
                reason.append(f"Face {duration:.1f}min < {MIN_DURATION}min")
            log(f"  [!] {student_name}: {', '.join(reason)} → ABSENT")
        
        # Check if attendance record already exists
        cursor.execute("""
            SELECT id FROM attendance 
            WHERE student_id = ? AND subject_id = ? AND date = ?
        """, (student_id, subj_id, today))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE attendance SET status = ?
                WHERE student_id = ? AND subject_id = ? AND date = ?
            """, (status, student_id, subj_id, today))
        else:
            cursor.execute("""
                INSERT INTO attendance (student_id, subject_id, date, status)
                VALUES (?, ?, ?, ?)
            """, (student_id, subj_id, today, status))
    
    # Clear temporary logs for this session
    if subject_id:
        cursor.execute("DELETE FROM face_logs WHERE subject_id = ? AND date = ?", (subject_id, today))
    
    conn.commit()
    conn.close()
    
    log("-" * 50)
    log(f"RESULT: {present_count} Present, {absent_count} Absent")
    log("Attendance finalized!")
    
    return present_count, absent_count

if __name__ == "__main__":
    finalize_attendance()
