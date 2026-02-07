"""
CREATE ADMIN ACCOUNT - Smart Attendance System
===============================================
Run this ONCE to create the admin account.
All other users (teachers, students) should be added 
through the Admin Panel in the web interface.

Usage:
    cd dev_tools
    python add_sample_users.py
"""

import sqlite3
import os

# Connect to database in parent directory
db_path = os.path.join(os.path.dirname(__file__), "..", "database.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Only create the admin account
# All other users will be added via Admin Panel
try:
    cursor.execute("""
        INSERT INTO users (name, email, password, role) 
        VALUES (?, ?, ?, ?)
    """, ("Admin", "admin@gmail.com", "admin", "admin"))
    print("[OK] Admin account created!")
    print("")
    print("Login credentials:")
    print("  Email: admin@gmail.com")
    print("  Password: admin")
    print("")
    print("Now login and add teachers/students via Admin Panel.")
except sqlite3.IntegrityError:
    print("[!] Admin account already exists.")
    print("  Email: admin@gmail.com")
    print("  Password: admin")

conn.commit()
conn.close()
