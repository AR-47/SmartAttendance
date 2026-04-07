"""
RFID SERVICE - Smart Attendance System
=======================================
This runs in background and captures RFID card taps.
Saves the latest scanned UID to a buffer table for use by the web app.

RFID readers send characters very fast (< 50ms between keys).
Human typing is much slower (> 100ms between keys).
We use this timing difference to filter out human typing.

Run in background:
    python rfid_service.py

Requirements:
    pip install keyboard
"""

import keyboard
import sqlite3
import os
import time
from datetime import datetime

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# Buffer to accumulate key presses
buffer = ""
last_key_time = 0

# RFID readers send all characters within ~50ms
# Human typing gaps are typically > 100ms
MAX_GAP_MS = 80  # Max gap between RFID characters (milliseconds)
MIN_UID_LENGTH = 6  # Minimum length of a valid RFID UID

def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def save_latest_uid(uid):
    """Save the latest card UID to buffer table"""
    uid = uid.strip()
    if not uid or len(uid) < MIN_UID_LENGTH:
        return
    
    # Only save if it looks like a UID (digits only)
    if not uid.isdigit():
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear old buffer and save new UID
    cursor.execute("DELETE FROM rfid_buffer")
    cursor.execute("INSERT INTO rfid_buffer (uid) VALUES (?)", (uid,))
    
    conn.commit()
    conn.close()
    
    log(f"[OK] Card captured: {uid}")
    log("     Ready to assign to user!")

def on_key(event):
    """Handle keyboard events from RFID reader"""
    global buffer, last_key_time
    
    current_time = time.time() * 1000  # milliseconds
    gap = current_time - last_key_time
    
    if event.name == "enter":
        if buffer and len(buffer) >= MIN_UID_LENGTH:
            save_latest_uid(buffer)
        buffer = ""
    elif len(event.name) == 1:  # Single character
        # If gap is too long, this is human typing — reset buffer
        if last_key_time > 0 and gap > MAX_GAP_MS:
            buffer = ""
        buffer += event.name
    
    last_key_time = current_time

def main():
    global buffer
    
    print("")
    print("=" * 60)
    print("   SMART ATTENDANCE - RFID SERVICE")
    print("   Captures cards for user registration")
    print("=" * 60)
    print("")
    log("RFID service started. Waiting for card taps...")
    log(f"Filter: Only captures fast input (< {MAX_GAP_MS}ms gap)")
    log(f"Filter: Only numeric UIDs with {MIN_UID_LENGTH}+ digits")
    log("Human typing on keyboard will be IGNORED.")
    print("")
    
    # Start listening for keyboard events
    keyboard.on_press(on_key)
    
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        log("RFID service stopped.")

if __name__ == "__main__":
    main()
