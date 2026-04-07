import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
ATTENDANCE_PERCENTAGE = 0.75 

def calculate_required_minutes(cursor, subject_id):
    """Calculates 75% of the scheduled class duration for the CURRENT session"""
    now = datetime.now()
    day, current_time = now.strftime("%A"), now.strftime("%H:%M")
    
    # Check for the slot that just ended (within the last 10 minutes) or is currently active
    cursor.execute("""
        SELECT start_time, end_time FROM timetable 
        WHERE subject_id = ? AND day = ? 
        ORDER BY ABS(strftime('%s', end_time) - strftime('%s', ?)) ASC LIMIT 1
    """, (subject_id, day, current_time))
    
    row = cursor.fetchone()
    if not row: return 30 # Fallback
    
    fmt = "%H:%M"
    total_minutes = (datetime.strptime(row['end_time'], fmt) - datetime.strptime(row['start_time'], fmt)).total_seconds() / 60
    return total_minutes * ATTENDANCE_PERCENTAGE

def finalize_attendance(subject_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT DISTINCT subject_id FROM face_logs WHERE date = ?", (today,))
    subjects = [row['subject_id'] for row in cursor.fetchall()]

    for sid in subjects:
        req_min = calculate_required_minutes(cursor, sid)
        
        # Get RFID and Face logs
        rfid_ids = {r['student_id'] for r in cursor.execute("SELECT student_id FROM rfid_logs WHERE subject_id=? AND DATE(timestamp)=?", (sid, today)).fetchall()}
        face_logs = cursor.execute("SELECT student_id, duration FROM face_logs WHERE subject_id=? AND date=?", (sid, today)).fetchall()

        for log in face_logs:
            status = "Present" if (log['student_id'] in rfid_ids and log['duration'] >= req_min) else "Absent"
            
            # Save to final attendance
            cursor.execute("INSERT INTO attendance (student_id, subject_id, date, status) VALUES (?, ?, ?, ?) ON CONFLICT DO UPDATE SET status=excluded.status", (log['student_id'], sid, today, status))
        
        cursor.execute("DELETE FROM face_logs WHERE subject_id=? AND date=?", (sid, today))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    finalize_attendance()