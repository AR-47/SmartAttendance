import cv2
import numpy as np
import os
import time
import sys
import threading
import sqlite3
import subprocess
import signal
from deepface import DeepFace
from datetime import datetime
import customtkinter as ctk
from PIL import Image, ImageTk
from pynput import keyboard

# -------- 1. SYSTEM CONFIGURATION & PATHS --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
FACE_DB_PATH = os.path.join(BASE_DIR, "id_database")

# Capture Subject ID from auto_scheduler.py
SUBJECT_ID = int(sys.argv[1]) if len(sys.argv) > 1 else None

# Recognition Settings
THRESHOLD = 0.50
MODEL_NAME = "ArcFace"
DETECTOR = "yunet"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LiveAttendanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Attendance - Live AI & RFID Monitor")
        self.geometry("1200x750")

        # --- INTERNAL STATE ---
        self.running = True
        self.known_faces = []
        self.rfid_to_id = {}
        self.tapped_student_ids = set()
        self.presence_counter = {}
        self.first_seen_time = {}
        self.last_seen_time = {}
        self.rfid_input_buffer = ""
        self.class_end_time = None 
        self.cap = None
        
        # --- UI LAYOUT ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="SMART\nATTENDANCE", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.pack(pady=30)

        status_text = f"Subject ID: {SUBJECT_ID}" if SUBJECT_ID else "Manual Mode"
        self.info_label = ctk.CTkLabel(self.sidebar, text=status_text, text_color="#38bdf8")
        self.info_label.pack(pady=10)
        
        self.timer_label = ctk.CTkLabel(self.sidebar, text="End Time: --:--", text_color="gray")
        self.timer_label.pack(pady=5)

        self.btn_stop = ctk.CTkButton(self.sidebar, text="STOP & FINALIZE", command=self.stop_and_exit, fg_color="#e74c3c", hover_color="#c0392b")
        self.btn_stop.pack(pady=20, padx=20)

        # Video Frame
        self.video_container = ctk.CTkFrame(self, corner_radius=15)
        self.video_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.video_label = ctk.CTkLabel(self.video_container, text="Starting Camera...")
        self.video_label.pack(expand=True, fill="both")

        # Signal Handling for Scheduler
        signal.signal(signal.SIGINT, lambda s, f: self.stop_and_exit())
        signal.signal(signal.SIGTERM, lambda s, f: self.stop_and_exit())

        # --- INITIALIZE ---
        self.load_system_data()
        self.start_camera_thread()
        self.start_rfid_listener()
        self.protocol("WM_DELETE_WINDOW", self.stop_and_exit)

    def load_system_data(self):
        """Fetch Student Data and the CURRENT session's End Time"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Map Names to IDs
        name_to_id_map = {s['name'].lower(): s['id'] for s in cursor.execute("SELECT id, name FROM users WHERE role = 'student'")}
        for s in cursor.execute("SELECT id, rfid_uid FROM users WHERE rfid_uid IS NOT NULL"):
            self.rfid_to_id[str(s['rfid_uid'])] = s['id']

        # 2. ROBUST TIME LOOKUP: Only get the end_time for the ACTIVE slot
        if SUBJECT_ID:
            now = datetime.now()
            day, current_time = now.strftime("%A"), now.strftime("%H:%M")
            cursor.execute("""
                SELECT end_time FROM timetable 
                WHERE subject_id = ? AND day = ? AND start_time <= ? AND end_time > ? 
                LIMIT 1
            """, (SUBJECT_ID, day, current_time, current_time))
            
            row = cursor.fetchone()
            if row:
                self.class_end_time = row['end_time']
                self.timer_label.configure(text=f"Ends at: {self.class_end_time}", text_color="#facc15")

        # 3. Load Faces and link to IDs
        for filename in os.listdir(FACE_DB_PATH):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                name = os.path.splitext(filename)[0]
                res = DeepFace.represent(os.path.join(FACE_DB_PATH, filename), model_name=MODEL_NAME, enforce_detection=False)
                self.known_faces.append({"name": name, "id": name_to_id_map.get(name.lower(), name), "embedding": res[0]["embedding"]})
                self.presence_counter[name] = 0
                self.first_seen_time[name] = self.last_seen_time[name] = None
        conn.close()

    def start_rfid_listener(self):
        """Background listener for RFID card taps"""
        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char is not None:
                    if key.char.isdigit():
                        self.rfid_input_buffer += key.char
                elif key == keyboard.Key.enter:
                    self.process_rfid_tap(self.rfid_input_buffer)
                    self.rfid_input_buffer = ""
            except: pass

        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()

    def process_rfid_tap(self, uid):
        """Link RFID tap to student and log to DB"""
        if uid in self.rfid_to_id:
            student_id = self.rfid_to_id[uid]
            self.tapped_student_ids.add(student_id)
            if SUBJECT_ID:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO rfid_logs (student_id, subject_id, timestamp)
                        VALUES (?, ?, ?)
                    """, (student_id, SUBJECT_ID, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    conn.close()
                except: pass

    def start_camera_thread(self):
        """Threaded video capture to keep UI smooth"""
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        threading.Thread(target=self.video_stream_loop, daemon=True).start()

    def video_stream_loop(self):
        """Main recognition loop with anti-rigging checks"""
        last_check = 0
        current_faces = []
        
        while self.running:
            # Automatic Time-Based Shutdown (Anti-Rigging)
            current_time = datetime.now().strftime("%H:%M")
            if self.class_end_time and current_time >= self.class_end_time:
                # Use after() to safely trigger stop from a thread
                self.after(10, self.stop_and_exit)
                break

            ret, frame = self.cap.read()
            if not ret: break

            if time.time() - last_check >= 1:
                last_check = time.time()
                try:
                    small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
                    faces = DeepFace.represent(small, model_name=MODEL_NAME, detector_backend=DETECTOR, enforce_detection=False)
                    current_faces = []
                    
                    for f in faces:
                        best_id, best_name, min_dist = None, "Unknown", 1.0
                        for p in self.known_faces:
                            dist = 1 - (np.dot(p["embedding"], f["embedding"]) / (np.linalg.norm(p["embedding"]) * np.linalg.norm(f["embedding"])))
                            if dist < min_dist and dist <= THRESHOLD:
                                min_dist, best_id, best_name = dist, p["id"], p["name"]
                        
                        # Only track if RFID tapped
                        is_verified = best_id in self.tapped_student_ids
                        if is_verified:
                            now = datetime.now()
                            if self.first_seen_time[best_name] is None:
                                self.first_seen_time[best_name] = now
                            self.last_seen_time[best_name] = now
                            self.presence_counter[best_name] += 1
                            self.update_live_db(best_id, best_name, round(self.presence_counter[best_name] / 60, 2))
                            
                        current_faces.append({"area": f["facial_area"], "name": best_name, "id": best_id, "verified": is_verified})
                except: current_faces = []

            for f in current_faces:
                a = f["area"]
                x, y, w, h = [v * 2 for v in [a['x'], a['y'], a['w'], a['h']]]
                color = (0, 255, 0) if f["verified"] else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                status = f"{f['name']} ({self.presence_counter.get(f['name'], 0)}s)" if f["verified"] else "TAP RFID"
                cv2.putText(frame, status, (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # SAFE GUI UPDATE: Try-Except prevents crash on exit
            if not self.running: break
            try:
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img)
                cw, ch = self.video_container.winfo_width(), self.video_container.winfo_height()
                if cw > 100: 
                    img_pil = img_pil.resize((cw - 20, ch - 20), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img_pil)
                self.video_label.configure(image=imgtk, text="")
                self.video_label.image = imgtk
            except: break

        if self.cap: self.cap.release()

    def update_live_db(self, student_id, name, duration):
        """Keep the real-time web dashboard updated"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT student_id FROM live_attendance WHERE student_id = ?", (str(student_id),))
            if cursor.fetchone() is None:
                now_str = datetime.now().strftime("%H:%M:%S")
                cursor.execute("""
                    INSERT INTO live_attendance (student_id, name, face_entry, face_exit, duration, status)
                    VALUES (?, ?, ?, ?, ?, 'Present')
                """, (str(student_id), name, now_str, now_str, duration))
            else:
                cursor.execute("UPDATE live_attendance SET duration = ?, face_exit = ? WHERE student_id = ?", 
                               (duration, datetime.now().strftime("%H:%M:%S"), str(student_id)))
            conn.commit()
            conn.close()
        except: pass

    def stop_and_exit(self):
        """Finalize logs and trigger the merge script"""
        if not self.running: return
        self.running = False
        time.sleep(0.5)
        
        # Save total face duration before closing
        if SUBJECT_ID:
            self.save_final_logs_to_db()
            try: 
                subprocess.run(["python", "finalize_attendance.py"], cwd=BASE_DIR)
            except: pass
            
        self.destroy()
        sys.exit()

    def save_final_logs_to_db(self):
        """Move session data to permanent face_logs"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        for p in self.known_faces:
            dur_min = round(self.presence_counter[p['name']] / 60, 2)
            cursor.execute("""
                INSERT INTO face_logs (student_id, subject_id, duration, date) 
                VALUES (?, ?, ?, ?)
            """, (p['id'], SUBJECT_ID, dur_min, today))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    app = LiveAttendanceApp()
    app.mainloop()