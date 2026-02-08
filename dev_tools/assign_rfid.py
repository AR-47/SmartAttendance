"""
ASSIGN RFID TO STUDENTS - Smart Attendance System
=================================================
Use this script to assign RFID card UIDs to students.

How to use:
1. Open Notepad
2. Tap each student's card to get their UID
3. Update the rfid_cards dictionary below
4. Run this script

Usage:
    cd dev_tools
    python assign_rfid.py
"""

import sqlite3
import os

# Connect to database in parent directory
db_path = os.path.join(os.path.dirname(__file__), "..", "database.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ================= RFID CARD ASSIGNMENTS =================
# Format: "Student Name": "Card UID"
# Get UIDs by tapping cards in Notepad

rfid_cards = {
    "Adithya": "0006867071",      # Replace with actual UID
    "Shreyas": "0006823788",      # Replace with actual UID
    "Rakesh": "0006761374",       # Replace with actual UID
    # Add more students as needed
}

# ================= UPDATE DATABASE =================
print("Assigning RFID cards to students...")
print("")

for name, uid in rfid_cards.items():
    cursor.execute("UPDATE users SET rfid_uid = ? WHERE name = ?", (uid, name))
    if cursor.rowcount > 0:
        print(f"[OK] {name} -> {uid}")
    else:
        print(f"[!] Student '{name}' not found in database")

conn.commit()
conn.close()

print("")
print("=" * 50)
print("RFID assignment complete!")
print("")
print("To verify, check the database:")
print("  SELECT name, rfid_uid FROM users WHERE role='student'")
print("=" * 50)
