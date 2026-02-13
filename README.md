# 🎓 SMART ATTENDANCE SYSTEM

### AI Face Recognition + RFID Dual Authentication with Timetable Automation

A fully automated, multi-factor attendance platform that combines:

🧠 AI Face Recognition
📟 RFID Identity Verification
📅 Timetable-Based Automation

**No manual attendance. No teacher interaction. Fully autonomous.**

---

# 📁 PROJECT STRUCTURE

```
smart_attendance/
│
│   setup_full_system.py     # Run ONCE → Creates full database
│
│   auto_scheduler.py        # Brain: auto-starts classes by timetable
│   live_recognition.py      # AI face detection engine
│   finalize_attendance.py   # Merges RFID + Face logs
│   rfid_service.py          # Listens for RFID card taps
│
│   database.db              # SQLite database (auto-created)
│   README.md
│
├───backend/
│       app.py               # Flask web server
│
├───frontend/
│   ├───static/
│   │       style.css
│   │       schedule.js
│   │
│   └───templates/
│           login.html
│           student_dashboard.html
│           teacher_dashboard.html
│           admin_dashboard.html
│           admin_users.html
│           admin_timetable.html
│           admin_download.html
│           add_user.html
│           add_class.html
│           add_subject.html
│           edit_user.html
│           live_monitor.html
│           timetable.html
│
└───id_database/
        StudentName.png      # Face images (Name must match user name)
```

---

# 🚀 FIRST TIME SETUP (FROM SCRATCH)

## 1️⃣ Install Requirements

```bash
pip install flask opencv-python deepface openpyxl keyboard numpy
```

---

## 2️⃣ Create Full Database

```bash
python setup_full_system.py
```

This creates **ALL required tables**:

| Category   | Tables                              |
| ---------- | ----------------------------------- |
| Academic   | users, classes, subjects, timetable |
| Attendance | attendance, live_attendance         |
| Automation | rfid_logs, face_logs, rfid_buffer   |

It also creates the **default admin account**:

| Role  | Email           | Password |
| ----- | --------------- | -------- |
| Admin | admin@gmail.com | admin    |

---

# 🖥 DAILY SYSTEM STARTUP

Open **3 terminals** every day:

### Terminal 1 — Web Server

```bash
cd backend
python app.py
```

Open browser → http://127.0.0.1:5000

### Terminal 2 — Scheduler (Brain)

```bash
python auto_scheduler.py
```

### Terminal 3 — RFID Service

```bash
python rfid_service.py
```

**System is now fully automatic.**

---

# 🔧 ADMIN SETUP WORKFLOW

Login as **Admin** (admin@gmail.com / admin)

---

## STEP A — Add Class

Admin Dashboard → **Add Class**

Example:

- Class Name: `CSE Blockchain`
- Room: `8CBC-1`

---

## STEP B — Add Subjects

Admin Dashboard → **Add Subject**

- DBMS
- AIML
- OOPS
- Cloud Computing

---

## STEP C — Add Teachers

Admin Dashboard → **Add User**

- Role: **Teacher**
- Fill name, email, password

---

## STEP D — Add Students (Live RFID Capture)

Admin Dashboard → **Add User**

1. Enter name, email, password
2. Select Role = **Student**
3. Select Class
4. **Tap RFID card on reader**
5. Click **Add User + Assign RFID**

Card UID is stored automatically.

---

## STEP E — Add Student Face Images

Place photos inside `id_database/`:

```
id_database/
    Adithya.png
    Shreyas.png
```

**⚠️ Filename must exactly match student name**

---

## STEP F — Create Timetable

Admin Dashboard → **Manage Timetable**

Set:

- Day + Start Time + End Time
- Subject + Teacher + Class

This timetable controls the **entire automation**.

---

# 👩‍🏫 TEACHER WORKFLOW

Teacher logs in →

**Can:**

- ✔ View weekly timetable
- ✔ View live attendance monitor
- ✔ Download today's attendance report

**Cannot:**

- ❌ Start attendance manually
- ❌ Edit timetable

---

# 👨‍🎓 STUDENT WORKFLOW

Student logs in →

**Can:**

- ✔ View weekly timetable

System automatically marks attendance based on:

- RFID tap + Face presence duration

---

# 🎥 AUTOMATIC ATTENDANCE PROCESS

```
Class time begins (from timetable)
        ↓
auto_scheduler.py detects session
        ↓
live_recognition.py camera starts
        ↓
Students tap RFID → Entry logged
Camera detects face → Duration tracked
        ↓
Class ends
        ↓
finalize_attendance.py runs automatically
        ↓
Attendance stored in database
```

---

# 🧠 ATTENDANCE RULE

| RFID | Face Duration | Result      |
| ---- | ------------- | ----------- |
| ✅   | ≥ 30 minutes  | **PRESENT** |
| ❌   | Any           | ABSENT      |
| ✅   | < 30 minutes  | ABSENT      |

**Multi-factor verification = Impossible to fake!**

---

# 📥 REPORT DOWNLOADS

| Role    | Access                                    |
| ------- | ----------------------------------------- |
| Teacher | Download today's report for their subject |
| Admin   | Download report by class + date           |

Reports are **Excel files** (.xlsx)

---

# 🔩 HARDWARE REQUIRED

| Device      | Type                    |
| ----------- | ----------------------- |
| Camera      | USB/Built-in webcam     |
| RFID Reader | USB HID (keyboard mode) |
| RFID Cards  | 125kHz / 13.56MHz       |

---

# 🎯 WHAT MAKES THIS SYSTEM SMART

| Feature          | Traditional    | This System       |
| ---------------- | -------------- | ----------------- |
| Attendance Start | Teacher clicks | Auto by timetable |
| Verification     | Roll call      | AI + RFID         |
| Proxy            | Possible       | Impossible        |
| Teacher Work     | High           | Zero              |
| Reports          | Manual         | One-click         |

---

# 📊 DATABASE TABLES

| Table           | Purpose                           |
| --------------- | --------------------------------- |
| users           | All users with RFID UIDs          |
| classes         | Class sections                    |
| subjects        | Subject names                     |
| timetable       | Weekly schedule                   |
| attendance      | Final attendance records          |
| live_attendance | Real-time tracking                |
| face_logs       | Face duration per session         |
| rfid_logs       | RFID tap timestamps               |
| rfid_buffer     | Latest tapped card (registration) |

---

# 🔑 DEFAULT LOGIN

| Role  | Email           | Password |
| ----- | --------------- | -------- |
| Admin | admin@gmail.com | admin    |

---

# 👨‍💻 BUILT BY

**Adithya**

_Python • Flask • OpenCV • DeepFace • SQLite_

---

# 📋 QUICK REFERENCE

## First Time Setup

```bash
pip install flask opencv-python deepface openpyxl keyboard numpy
python setup_full_system.py
```

## Daily Startup

```bash
# Terminal 1
cd backend && python app.py

# Terminal 2
python auto_scheduler.py

# Terminal 3
python rfid_service.py
```

## Browser

http://127.0.0.1:5000

---

**🚀 System is production-ready!**
