"""
RFID SERVICE - Smart Attendance System
=======================================
This runs in background and captures RFID card taps.
Saves the latest scanned UID to a buffer table for use by the web app.

When admin clicks "Add User", Flask reads the last captured card UID.

Run in background:
    python rfid_service.py

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

def save_latest_uid(uid):
    """Save the latest card UID to buffer table"""
    uid = uid.strip()
    if not uid:
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
    global buffer
    
    if event.name == "enter":
        if buffer:
            save_latest_uid(buffer)
            buffer = ""
    elif event.name == "backspace":
        buffer = buffer[:-1]
    elif len(event.name) == 1:  # Single character
        buffer += event.name

def main():
    global buffer
    
    print("")
    print("=" * 60)
    print("   SMART ATTENDANCE - RFID SERVICE")
    print("   Captures cards for user registration")
    print("=" * 60)
    print("")
    log("RFID service started. Waiting for card taps...")
    log("Admin can now add users and tap cards to assign them.")
    print("")
    
    # Start listening for keyboard events
    keyboard.on_press(on_key)
    
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        log("RFID service stopped.")

if __name__ == "__main__":
    main()
