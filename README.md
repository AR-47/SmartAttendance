# 🎓 SMART ATTENDANCE SYSTEM

### AI-Powered Face Recognition Attendance with Timetable Integration

---

## 📁 PROJECT STRUCTURE

```
smart_attendance/
│   database.db              # SQLite database
│   live_recognition.py      # AI face recognition engine
│   auto_scheduler.py        # Auto-starts sessions by timetable
│
├───backend/
│       app.py               # Flask web server
│
├───frontend/
│   ├───static/
│   │       style.css        # Styling
│   │       schedule.js      # Timetable interactions
│   │
│   └───templates/
│           login.html
│           student_dashboard.html
│           teacher_dashboard.html
│           admin_dashboard.html
│           add_user.html
│           add_subject.html
│           add_class.html
│           admin_timetable.html
│           timetable.html
│
├───dev_tools/
│       setup_system_db.py   # Creates database tables
│       add_sample_users.py  # Adds test users
│
└───id_database/
        Adithya.png          # Face images for recognition
        (add more .png/.jpg files named as student names)
```

---

## 🚀 COMPLETE DEMO GUIDE (For Reviewers)

### STEP 1: Setup Database (One-time)

Open **PowerShell/Terminal** and run:

```powershell
cd c:\Users\adith\Desktop\smart_attendance\dev_tools
python setup_system_db.py
```

Expected output:

```
[OK] Database tables created successfully!
```

---

### STEP 2: Start Flask Server

Open a **new terminal** (keep it running):

```powershell
cd c:\Users\adith\Desktop\smart_attendance\backend
python app.py
```

Expected output:

```
 * Running on http://127.0.0.1:5000
```

---

### STEP 3: Create Admin Account (First Time)

You need at least one admin to use the system. Run:

```powershell
cd c:\Users\adith\Desktop\smart_attendance\dev_tools
python add_sample_users.py
```

This creates a default admin:

- **Email:** `admin@mail.com`
- **Password:** `admin`

---

### STEP 4: Login as Admin

1. Open browser: **http://127.0.0.1:5000/login**
2. Login with:
   - Email: `admin@mail.com`
   - Password: `admin`

You'll see the **Admin Dashboard** with stats.

---

### STEP 5: Add a Class

1. Click **"Add Class"**
2. Enter:
   - Class Name: `CSE Blockchain`
   - Section: `8CBC-1`
3. Click **Add Class**

---

### STEP 6: Add Subjects

1. Click **"Add Subject"** (from dashboard)
2. Add these subjects one by one:
   - `DBMS`
   - `AIML`
   - `OOPS`
   - `Cloud Computing`

---

### STEP 7: Add Teachers

1. Click **"Add User"**
2. Add teachers:

| Name   | Email            | Password | Role    |
| ------ | ---------------- | -------- | ------- |
| Stacey | stacey@gmail.com | 1234     | Teacher |
| Becky  | becky@gmail.com  | 1234     | Teacher |
| Keisha | keisha@gmail.com | 1234     | Teacher |
| Ashley | ashley@gmail.com | 1234     | Teacher |

---

### STEP 8: Add Students (Assign to Class)

1. Click **"Add User"**
2. Add students (select the class!):

| Name    | Email             | Password | Role    | Class                   |
| ------- | ----------------- | -------- | ------- | ----------------------- |
| Adithya | adithya@gmail.com | 1234     | Student | CSE Blockchain - 8CBC-1 |
| Shreyas | shreyas@gmail.com | 1234     | Student | CSE Blockchain - 8CBC-1 |
| Rakesh  | rakesh@gmail.com  | 1234     | Student | CSE Blockchain - 8CBC-1 |

---

### STEP 9: Create Timetable

1. Click **"Manage Timetable"**
2. Add time slots:

| Class          | Subject         | Teacher | Day     | Start | End   |
| -------------- | --------------- | ------- | ------- | ----- | ----- |
| CSE Blockchain | DBMS            | Stacey  | Monday  | 09:00 | 10:00 |
| CSE Blockchain | AIML            | Becky   | Monday  | 10:00 | 11:00 |
| CSE Blockchain | OOPS            | Keisha  | Tuesday | 09:00 | 10:00 |
| CSE Blockchain | Cloud Computing | Ashley  | Tuesday | 10:00 | 11:00 |

---

### STEP 10: Test Student Login

1. Logout
2. Login as student:
   - Email: `adithya@mail.com`
   - Password: `1234`
3. See the **timetable view**

---

### STEP 11: Test Teacher Login

1. Logout
2. Login as teacher:
   - Email: `stacey@mail.com`
   - Password: `1234`
3. See **assigned classes** with Start Attendance button

---

### STEP 12: Add Face Images

Add student face photos to: `id_database/`

- File name = Student name (e.g., `Adithya.png`, `Messi.jpg`)
- Clear front-facing photos work best

---

### STEP 13: Test Manual Face Recognition

```powershell
cd c:\Users\adith\Desktop\smart_attendance
python live_recognition.py
```

1. Click **Start Attendance**
2. Face the camera
3. See names appear above detected faces
4. Press **Q** to stop
5. Check the generated Excel report

---

### STEP 14: Run Auto Scheduler (Smart Mode)

Open a **new terminal**:

```powershell
cd c:\Users\adith\Desktop\smart_attendance
python auto_scheduler.py
```

The system now:

- ✅ Watches the timetable
- ✅ Auto-starts camera when class begins
- ✅ Auto-stops when class ends
- ✅ Tags attendance with subject + date

---

## 🔐 ACCESS CONTROL

| Role    | Can Add Users | Can Add Timetable | Can View Timetable | Can Start Attendance |
| ------- | ------------- | ----------------- | ------------------ | -------------------- |
| Admin   | ✅            | ✅                | ✅                 | ❌                   |
| Teacher | ❌            | ❌                | ✅ (own classes)   | ✅                   |
| Student | ❌            | ❌                | ✅ (own class)     | ❌                   |

---

## 🧠 SYSTEM FEATURES

### Core Features

- ✅ Face recognition using DeepFace AI
- ✅ Role-based authentication (Admin/Teacher/Student)
- ✅ Timetable management
- ✅ Subject-wise attendance tracking

### Smart Features

- ✅ Auto-scheduled attendance sessions
- ✅ Context-aware attendance (tagged by subject)
- ✅ Presence ratio calculation (not just yes/no)
- ✅ Entry/exit time tracking

---

## 📧 LOGIN CREDENTIALS (After Setup)

| Role    | Email            | Password |
| ------- | ---------------- | -------- |
| Admin   | admin@mail.com   | admin    |
| Teacher | stacey@mail.com  | 1234     |
| Student | adithya@mail.com | 1234     |

---

## ⚠️ REQUIREMENTS

- Python 3.8+
- Flask
- OpenCV
- DeepFace
- openpyxl
- tkinter (usually pre-installed)

Install with:

```bash
pip install flask opencv-python deepface openpyxl
```

---

## 🎯 WHAT MAKES THIS "SMART"

1. **Timetable-Driven** - No manual intervention needed
2. **Context-Aware** - Knows which subject is being attended
3. **AI-Powered** - Face recognition, not manual roll call
4. **Role-Based** - Each user sees only what they need
5. **Fully Automated** - Camera starts/stops on schedule

---

Built with ❤️ by Adithya
