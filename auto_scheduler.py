"""
AUTO SCHEDULER - The Brain of Smart Attendance System
=====================================================
This script runs continuously and automatically:
- Checks if there's a class scheduled RIGHT NOW
- Starts face recognition when class begins
- Stops it when class ends
- Works completely hands-free!

Run this script during college hours:
    python auto_scheduler.py
"""

import sqlite3
import subprocess
import time
import os
from datetime import datetime

# Database path
DB_PATH = "database.db"

# Track running state
running_process = None
current_session = None

def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_current_slot():
    """Check if there's a class scheduled right now"""
    now = datetime.now()
    day = now.strftime("%A")  # Monday, Tuesday, etc.
    current_time = now.strftime("%H:%M")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timetable.id, timetable.subject_id, subjects.subject_name, classes.class_name, 
               users.name as teacher, timetable.start_time, timetable.end_time
        FROM timetable
        JOIN subjects ON timetable.subject_id = subjects.id
        JOIN classes ON timetable.class_id = classes.id
        JOIN users ON timetable.teacher_id = users.id
        WHERE timetable.day = ? 
          AND timetable.start_time <= ? 
          AND timetable.end_time > ?
    """, (day, current_time, current_time))
    
    slot = cursor.fetchone()
    conn.close()
    
    return slot

def start_session(slot_info):
    """Start the face recognition camera"""
    global running_process
    
    slot_id, subject_id, subject, class_name, teacher, start, end = slot_info
    
    log("=" * 50)
    log(f"CLASS STARTED: {subject}")
    log(f"Class: {class_name} | Teacher: {teacher}")
    log(f"Time: {start} - {end}")
    log(f"Subject ID: {subject_id} (for attendance tagging)")
    log("Starting face recognition...")
    log("=" * 50)
    
    # Start live_recognition.py in background with subject_id
    script_path = os.path.join(os.path.dirname(__file__), "live_recognition.py")
    running_process = subprocess.Popen(
        ["python", script_path, str(subject_id)],
        cwd=os.path.dirname(script_path)
    )

def stop_session():
    """Stop the face recognition camera"""
    global running_process
    
    log("=" * 50)
    log("CLASS ENDED - Stopping attendance session")
    log("Attendance saved automatically!")
    log("=" * 50)
    
    if running_process:
        running_process.terminate()
        running_process = None

def main():
    global current_session
    
    print("")
    print("=" * 60)
    print("   SMART ATTENDANCE - AUTO SCHEDULER")
    print("   The system is now watching the timetable...")
    print("=" * 60)
    print("")
    log("Auto scheduler started. Checking every 30 seconds...")
    log(f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")
    print("")
    
    while True:
        try:
            slot = get_current_slot()
            
            # Class is happening now
            if slot:
                slot_id = slot[0]
                
                # New class started (different from current)
                if current_session != slot_id:
                    # Stop previous session if any
                    if current_session is not None:
                        stop_session()
                    
                    # Start new session
                    start_session(slot)
                    current_session = slot_id
            
            # No class right now
            else:
                if current_session is not None:
                    stop_session()
                    current_session = None
            
            # Wait before next check
            time.sleep(30)
            
        except KeyboardInterrupt:
            log("Scheduler stopped by user")
            if running_process:
                running_process.terminate()
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
