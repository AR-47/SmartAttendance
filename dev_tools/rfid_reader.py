"""
RFID READER - Smart Attendance System
======================================
This script runs in the background and captures RFID card taps.
Works with keyboard-output RFID readers.

How it works:
1. Student taps RFID card
2. Reader sends UID as keyboard input (ending with Enter)
3. Script captures UID and logs entry to database
4. Auto-tags with current subject from timetable

Run during class hours:
    python rfid_reader.py

Requirements:
    pip install keyboard
"""

import keyboard
import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

# Buffer to accumulate key presses
buffer = ""

def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_current_subject():
    """Get the currently running subject from timetable"""
    now = datetime.now()
    day = now.strftime("%A")
    current_time = now.strftime("%H:%M")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timetable.subject_id, subjects.subject_name
        FROM timetable
        JOIN subjects ON timetable.subject_id = subjects.id
        WHERE timetable.day = ? 
          AND timetable.start_time <= ? 
          AND timetable.end_time > ?
    """, (day, current_time, current_time))
    
    result = cursor.fetchone()
    conn.close()
    
    return result  # (subject_id, subject_name) or None

def process_uid(uid):
    """Process the captured RFID UID"""
    uid = uid.strip()
    if not uid:
        return
    
    log(f"Card detected: {uid}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find student by RFID
    cursor.execute("SELECT id, name FROM users WHERE rfid_uid = ?", (uid,))
    student = cursor.fetchone()
    
    if student:
        student_id = student["id"]
        student_name = student["name"]
        
        # Get current subject
        subject_info = get_current_subject()
        subject_id = subject_info[0] if subject_info else None
        subject_name = subject_info[1] if subject_info else "No class"
        
        # Log the RFID entry
        cursor.execute("""
            INSERT INTO rfid_logs (student_id, subject_id, timestamp)
            VALUES (?, ?, ?)
        """, (student_id, subject_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        log(f"[OK] {student_name} checked in for {subject_name}")
    else:
        log(f"[!] Unknown card: {uid}")
    
    conn.close()

def on_key(event):
    """Handle keyboard events from RFID reader"""
    global buffer
    
    if event.name == "enter":
        if buffer:
            process_uid(buffer)
            buffer = ""
    elif event.name == "backspace":
        buffer = buffer[:-1]
    elif len(event.name) == 1:  # Single character (digit or letter)
        buffer += event.name

def main():
    global buffer
    
    print("")
    print("=" * 60)
    print("   SMART ATTENDANCE - RFID READER")
    print("   Waiting for card taps...")
    print("=" * 60)
    print("")
    log("RFID reader started. Press Ctrl+C to stop.")
    print("")
    
    # Start listening for keyboard events
    keyboard.on_press(on_key)
    
    try:
        keyboard.wait()  # Run forever until interrupted
    except KeyboardInterrupt:
        log("RFID reader stopped.")

if __name__ == "__main__":
    main()
