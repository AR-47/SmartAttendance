import cv2
import numpy as np
import os
import time
import sys
from deepface import DeepFace
from datetime import datetime
import openpyxl
import tkinter as tk
from threading import Thread
import sqlite3

# -------- SUBJECT ID FROM SCHEDULER --------
# When called from auto_scheduler.py, subject_id is passed as argument
SUBJECT_ID = int(sys.argv[1]) if len(sys.argv) > 1 else None

# -------- GLOBAL CONTROL --------
running = False

# -------- FACE ATTENDANCE --------
def run_attendance():
    global running

    DB_PATH = "id_database"
    THRESHOLD = 0.50
    MODEL_NAME = "ArcFace"
    DETECTOR = "yunet"

    CLASS_DURATION_MIN = 60
    REQUIRED_PRESENT_MIN = 50
    CHECK_INTERVAL = 1

    now = datetime.now()
    session_date = str(now.date())
    session_hour = now.strftime("%H-00")
    EXCEL_FILE = f"attendance_{session_date}_{session_hour}.xlsx"

    known_faces = []
    presence_counter = {}
    first_seen_time = {}
    last_seen_time = {}
    total_checks = 0

    print("Loading face database...")

    for filename in os.listdir(DB_PATH):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(DB_PATH, filename)
            parts = os.path.splitext(filename)[0].split('_')
            sid = parts[0]
            name = parts[1] if len(parts) > 1 else parts[0]

            results = DeepFace.represent(img_path=img_path, model_name=MODEL_NAME, enforce_detection=False)
            known_faces.append({"name": name, "id": sid, "embedding": results[0]["embedding"]})
            presence_counter[name] = 0
            first_seen_time[name] = None
            last_seen_time[name] = None

    def get_distance(v1, v2):
        return 1 - (np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

    cap = cv2.VideoCapture(0)
    start_time = time.time()
    last_check_time = 0

    print("Attendance session started...")

    # Database connection for live updates
    conn = sqlite3.connect("database.db", check_same_thread=False)
    cursor = conn.cursor()

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        # Stop after class duration
        if (time.time() - start_time) / 60 >= CLASS_DURATION_MIN:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

        if time.time() - last_check_time >= CHECK_INTERVAL:
            total_checks += 1
            last_check_time = time.time()

            try:
                faces = DeepFace.represent(
                    img_path=small_frame,
                    model_name=MODEL_NAME,
                    detector_backend=DETECTOR,
                    enforce_detection=False,
                    align=True
                )

                seen = set()

                for face in faces:
                    live_embedding = face["embedding"]
                    best_match = "Unknown"
                    min_dist = 1.0

                    for person in known_faces:
                        dist = get_distance(person["embedding"], live_embedding)
                        if dist < min_dist and dist <= THRESHOLD:
                            min_dist = dist
                            best_match = person["name"]

                    # Attendance timing logic
                    if best_match != "Unknown":
                        seen.add(best_match)
                        now_dt = datetime.now()
                        if first_seen_time[best_match] is None:
                            first_seen_time[best_match] = now_dt
                        last_seen_time[best_match] = now_dt

                        # Update database with live attendance
                        # Check if student already exists in DB
                        cursor.execute("SELECT face_entry FROM live_attendance WHERE student_id = ?", (person["id"],))
                        row = cursor.fetchone()

                        entry = first_seen_time[best_match].strftime("%H:%M:%S")
                        exit_time = last_seen_time[best_match].strftime("%H:%M:%S")
                        duration = round((last_seen_time[best_match] - first_seen_time[best_match]).total_seconds()/60, 2)

                        if row is None:
                            # First time seeing this student → INSERT
                            cursor.execute("""
                                INSERT INTO live_attendance (student_id, name, face_entry, face_exit, duration, status)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (person["id"], best_match, entry, exit_time, duration, "Present"))
                        else:
                            # Already exists → UPDATE only exit time + duration
                            cursor.execute("""
                                UPDATE live_attendance
                                SET face_exit = ?, duration = ?, status = ?
                                WHERE student_id = ?
                            """, (exit_time, duration, "Present", person["id"]))

                        conn.commit()


                    # -------- DRAW FACE BOX --------
                    area = face["facial_area"]
                    x, y, w, h = [v * 2 for v in [area['x'], area['y'], area['w'], area['h']]]

                    color = (0, 255, 0) if best_match != "Unknown" else (0, 0, 255)

                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, best_match, (x, y-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                for name in seen:
                    presence_counter[name] += 1

            except:
                pass

        cv2.imshow("Face Attendance System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    running = False

    generate_report(known_faces, presence_counter, first_seen_time,
                    last_seen_time, total_checks,
                    REQUIRED_PRESENT_MIN, CLASS_DURATION_MIN,
                    EXCEL_FILE)

# -------- REPORT GENERATION --------
def generate_report(known_faces, presence_counter, first_seen_time,
                    last_seen_time, total_checks,
                    REQUIRED_PRESENT_MIN, CLASS_DURATION_MIN,
                    EXCEL_FILE):

    required_ratio = REQUIRED_PRESENT_MIN / CLASS_DURATION_MIN
    wb = openpyxl.Workbook()
    ws = wb.active

    ws.append(["Student Name","Student ID","Face Entry",
               "Face Exit","Duration (Minutes)","Status"])

    for person in known_faces:
        name = person["name"]
        sid = person["id"]
        ratio = presence_counter[name] / total_checks if total_checks else 0

        entry = first_seen_time[name]
        exit = last_seen_time[name]

        entry_str = entry.strftime("%H:%M:%S") if entry else "-"
        exit_str = exit.strftime("%H:%M:%S") if exit else "-"
        duration = round((exit-entry).total_seconds()/60,2) if entry and exit else 0

        status = "Present" if ratio >= required_ratio else "Absent"

    ws.append([name, sid, entry_str, exit_str, duration, status])

    wb.save(EXCEL_FILE)
    print(f"Attendance saved to {EXCEL_FILE}")
    
    # -------- SAVE TO DATABASE WITH SUBJECT --------
    if SUBJECT_ID:
        save_attendance_to_db(known_faces, presence_counter, total_checks, required_ratio)

def save_attendance_to_db(known_faces, presence_counter, total_checks, required_ratio):
    """Save attendance to database with subject tagging"""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    for person in known_faces:
        name = person["name"]
        sid = person["id"]
        ratio = presence_counter[name] / total_checks if total_checks else 0
        status = "Present" if ratio >= required_ratio else "Absent"
        
        # Check if record already exists for this student, subject, and date
        cursor.execute("""
            SELECT id FROM attendance 
            WHERE student_id = ? AND subject_id = ? AND date = ?
        """, (sid, SUBJECT_ID, today))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute("""
                UPDATE attendance SET status = ? 
                WHERE student_id = ? AND subject_id = ? AND date = ?
            """, (status, sid, SUBJECT_ID, today))
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO attendance (student_id, subject_id, date, status)
                VALUES (?, ?, ?, ?)
            """, (sid, SUBJECT_ID, today, status))
    
    conn.commit()
    conn.close()
    print(f"[DB] Attendance saved to database for Subject ID: {SUBJECT_ID}")

# -------- GUI --------
def start_attendance():
    global running
    if not running:
        running = True
        Thread(target=run_attendance).start()

def stop_program():
    global running
    running = False

root = tk.Tk()
root.title("Face Attendance Dashboard")
root.geometry("400x250")

tk.Label(root, text="AI Face Attendance System", font=("Arial",16)).pack(pady=20)
tk.Button(root, text="Start Attendance", command=start_attendance).pack(pady=10)
tk.Button(root, text="Stop", command=stop_program).pack(pady=10)

root.mainloop()