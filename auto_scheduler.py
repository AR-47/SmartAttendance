import sqlite3
import subprocess
import time
import os
import signal
from datetime import datetime

# Resolve all paths relative to THIS script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

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
    day = now.strftime("%A")
    current_time = now.strftime("%H:%M")
    
    try:
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
    except Exception as e:
        log(f"DB Error: {e}")
        return None

def start_session(slot_info):
    """Start the face recognition camera"""
    global running_process
    slot_id, subject_id, subject, class_name, teacher, start, end = slot_info
    
    log("=" * 50)
    log(f"CLASS STARTED: {subject}")
    log(f"Class: {class_name} | Teacher: {teacher}")
    log(f"Time: {start} - {end}")
    log("Starting face recognition...")
    log("=" * 50)
    
    script_path = os.path.join(BASE_DIR, "live_recognition.py")
    
    try:
        # Start live_recognition.py in background with subject_id
        running_process = subprocess.Popen(
            ["python", script_path, str(subject_id)],
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        log(f"Camera process started (PID: {running_process.pid})")
    except Exception as e:
        log(f"ERROR starting camera: {e}")
        running_process = None

def stop_session():
    """Stop the face recognition camera gracefully"""
    global running_process
    
    log("=" * 50)
    log("CLASS ENDED - Stopping attendance session")
    log("=" * 50)
    
    if running_process:
        try:
            # Send signal for graceful shutdown to trigger DB saving
            running_process.send_signal(signal.CTRL_C_EVENT)
            
            log("Waiting for attendance to save in Database...")
            running_process.wait(timeout=60) # Allow time for face_logs and finalize_attendance
            log("Attendance saved and finalized!")
        except subprocess.TimeoutExpired:
            log("Timeout - force stopping process...")
            running_process.terminate()
        except Exception as e:
            log(f"Stop error: {e}")
            running_process.terminate()
        
        running_process = None

def main():
    global current_session
    
    print("")
    print("=" * 60)
    print("   SMART ATTENDANCE - AUTO SCHEDULER (V2)")
    print("   High-Frequency Monitoring Active")
    print("=" * 60)
    print("")
    log(f"Base directory: {BASE_DIR}")
    log(f"Database: {DB_PATH}")
    log(f"Auto scheduler started. Checking every 1 second...") # Updated log message
    log(f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")
    print("")
    
    while True:
        try:
            slot = get_current_slot()
            
            if slot:
                slot_id = slot[0]
                # New class started or different session
                if current_session != slot_id:
                    if current_session is not None:
                        stop_session()
                    start_session(slot)
                    current_session = slot_id
            else:
                # No class happening now
                if current_session is not None:
                    stop_session()
                    current_session = None
            
            # Use 1 second for near-instant detection
            time.sleep(1) 
            
        except KeyboardInterrupt:
            log("Scheduler stopped by user")
            if running_process:
                running_process.terminate()
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()