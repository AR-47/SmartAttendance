import sqlite3
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM face_logs")
cursor.execute("DELETE FROM rfid_logs")
cursor.execute("DELETE FROM live_attendance")
conn.commit()
conn.close()
print("Logs cleared. System ready for a fresh start.")