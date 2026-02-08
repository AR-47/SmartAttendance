# 🎓 SMART ATTENDANCE SYSTEM

### AI-Powered Face Recognition + RFID Attendance with Timetable Integration

A fully automated attendance system that uses **AI face recognition** and **RFID verification** to track student presence. The system runs autonomously based on the class timetable — no manual intervention required.

---

## ✨ Key Features

| Feature                    | Description                                  |
| -------------------------- | -------------------------------------------- |
| 🤖 **AI Face Recognition** | DeepFace-powered real-time face detection    |
| 📟 **RFID Integration**    | Hardware card verification for entry logging |
| 📅 **Timetable-Driven**    | Auto-starts/stops based on class schedule    |
| 🔐 **Role-Based Access**   | Admin, Teacher, Student dashboards           |
| 📊 **Live Monitoring**     | Real-time attendance view                    |
| 🏷️ **Subject-Tagged**      | Attendance linked to specific subjects       |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SMART ATTENDANCE SYSTEM                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   📅 Timetable Database                                      │
│        ↓                                                     │
│   ⏰ Auto Scheduler (watches clock, controls sessions)       │
│        ↓                                                     │
│   ┌──────────────────┐    ┌──────────────────┐              │
│   │  🎥 Face AI      │    │  📟 RFID Reader  │              │
│   │  (presence)      │    │  (entry verify)  │              │
│   └────────┬─────────┘    └────────┬─────────┘              │
│            └──────────┬────────────┘                         │
│                       ↓                                      │
│               💾 Attendance Database                         │
│               (student_id + subject_id + date)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
smart_attendance/
│
│   # ====== CORE RUNTIME ======
│   auto_scheduler.py        # Brain: auto-starts sessions by timetable
│   live_recognition.py      # AI face recognition engine
│   rfid_service.py          # RFID capture for user registration
│   database.db              # SQLite database
│   README.md                # This file
│
├───backend/
│       app.py               # Flask web server (all routes)
│
├───frontend/
│   ├───static/
│   │       style.css        # Dark theme styling
│   │       schedule.js      # Timetable interactions
│   │
│   └───templates/
│           login.html
│           student_dashboard.html
│           teacher_dashboard.html
│           admin_dashboard.html
│           admin_users.html
│           admin_timetable.html
│           add_user.html
│           add_class.html
│           add_subject.html
│           edit_user.html
│           live_monitor.html
│           timetable.html
│
├───dev_tools/               # One-time setup scripts
│       setup_system_db.py   # Creates database tables
│       add_sample_users.py  # Creates admin account
│       setup_rfid.py        # Adds RFID tables
│       assign_rfid.py       # Manual RFID assignment
│       rfid_reader.py       # Standalone RFID logging
│
└───id_database/             # Face images for recognition
        Adithya.png
        (add more student photos here)
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install flask opencv-python deepface openpyxl keyboard
```

### 2. Setup Database

```bash
cd dev_tools
python setup_system_db.py    # Create tables
python add_sample_users.py   # Create admin account
python setup_rfid.py         # Add RFID support
```

### 3. Run the System

**Terminal 1: Web Server**

```bash
cd backend
python app.py
```

**Terminal 2: Auto Scheduler**

```bash
python auto_scheduler.py
```

**Terminal 3: RFID Service** (optional, for registration)

```bash
python rfid_service.py
```

### 4. Access the System

Open browser: **http://127.0.0.1:5000**

---

## 🔑 Default Login

| Role  | Email           | Password |
| ----- | --------------- | -------- |
| Admin | admin@gmail.com | admin    |

---

## 📋 Setup Workflow (For Demo)

1. **Login as Admin**
2. **Add Classes** → CSE Blockchain - 8CBC-1
3. **Add Subjects** → DBMS, AIML, OOPS, Cloud Computing
4. **Add Teachers** → With email and password
5. **Add Students** → Assign to class, tap RFID card
6. **Create Timetable** → Assign subjects to time slots
7. **Add Face Photos** → Put student photos in `id_database/`
8. **Run auto_scheduler.py** → System now runs automatically!

---

## 🎯 How It Works

### Fully Automated Flow:

```
09:00 → Timetable says "DBMS class starts"
      → Auto Scheduler detects this
      → Launches face recognition camera
      → Students walk in, faces detected
      → 10:00 → Class ends → Camera stops
      → Attendance saved with subject tag
```

**Zero teacher intervention required.**

---

## 👥 Role Permissions

| Feature           | Admin | Teacher | Student |
| ----------------- | ----- | ------- | ------- |
| Add Users         | ✅    | ❌      | ❌      |
| Add Classes       | ✅    | ❌      | ❌      |
| Add Subjects      | ✅    | ❌      | ❌      |
| Manage Timetable  | ✅    | ❌      | ❌      |
| View Own Schedule | ✅    | ✅      | ✅      |
| View Live Monitor | ✅    | ✅      | ❌      |
| Reset Passwords   | ✅    | ❌      | ❌      |

---

## 🔧 Hardware Requirements

| Component         | Purpose           |
| ----------------- | ----------------- |
| Webcam            | Face recognition  |
| RFID Reader (USB) | Card verification |
| RFID Cards        | Student ID cards  |

**RFID Reader Type:** USB HID (keyboard output mode)

---

## 📊 Database Schema

```sql
users       → id, name, email, password, role, class_id, rfid_uid
classes     → id, class_name, room_no
subjects    → id, subject_name
timetable   → id, class_id, subject_id, teacher_id, day, start_time, end_time
attendance  → id, student_id, subject_id, date, status
rfid_logs   → id, student_id, subject_id, timestamp
```

---

## 🆚 What Makes This "Smart"

| Regular System        | This System               |
| --------------------- | ------------------------- |
| Teacher clicks button | Auto-starts by timetable  |
| Manual roll call      | AI face recognition       |
| No verification       | RFID + Face dual auth     |
| Generic records       | Subject-tagged attendance |
| Needs supervision     | Runs autonomously         |

---

## 🛡️ Security Notes

- Passwords are stored in plain text (for demo purposes)
- For production: Use `werkzeug.security` for hashing
- RFID UIDs should be encrypted in production

---

## 📝 Future Improvements

- [ ] Password hashing
- [ ] Email notifications for absences
- [ ] Attendance reports export
- [ ] Mobile app for students
- [ ] Multiple camera support
- [ ] Cloud deployment

---

## 👨‍💻 Built By

**Adithya**

---

## 📜 License

This project is for educational purposes.

---

_Built with Flask, OpenCV, DeepFace, and SQLite_ 🐍
