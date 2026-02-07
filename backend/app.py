from flask import Flask, render_template, jsonify, request, redirect, session, url_for
import sqlite3
import os
import subprocess

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

app.secret_key = "supersecretkey"

DB_PATH = "../database.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# -------- LOGIN SYSTEM --------
def validate_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, name FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = validate_user(email, password)

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = user["name"]

            if user["role"] == "student":
                return redirect("/student")
            elif user["role"] == "teacher":
                return redirect("/teacher")
            else:
                return redirect("/admin")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html", error="")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -------- ROLE DASHBOARDS --------
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/login")

    student_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    # Get student's class
    cursor.execute("SELECT class_id FROM users WHERE id=?", (student_id,))
    result = cursor.fetchone()
    class_id = result["class_id"] if result and result["class_id"] else None

    # Initialize grid data
    timetable = {}
    timeslots = set()
    class_name = ""

    if class_id:
        # Get class name
        cursor.execute("SELECT class_name, room_no FROM classes WHERE id=?", (class_id,))
        class_info = cursor.fetchone()
        if class_info:
            class_name = f"{class_info['class_name']} - {class_info['room_no']}"

        # Get timetable for that class
        cursor.execute("""
            SELECT timetable.day, timetable.start_time, timetable.end_time, subjects.subject_name
            FROM timetable
            JOIN subjects ON timetable.subject_id = subjects.id
            WHERE timetable.class_id = ?
        """, (class_id,))
        rows = cursor.fetchall()

        # Convert to grid dictionary: {(day, time_range): subject_name}
        for r in rows:
            day = r["day"]
            time_range = f"{r['start_time']} - {r['end_time']}"
            timetable[(day, time_range)] = r["subject_name"]
            timeslots.add(time_range)

    conn.close()

    # Sort timeslots by start time
    timeslots = sorted(list(timeslots))

    return render_template("student_dashboard.html",
                           name=session["name"],
                           class_name=class_name,
                           timetable=timetable,
                           timeslots=timeslots)

@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/login")

    teacher_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timetable.day, timetable.start_time, timetable.end_time,
               subjects.subject_name, classes.class_name, classes.room_no
        FROM timetable
        JOIN subjects ON timetable.subject_id = subjects.id
        JOIN classes ON timetable.class_id = classes.id
        WHERE timetable.teacher_id = ?
    """, (teacher_id,))

    rows = cursor.fetchall()
    conn.close()

    # Convert to grid dictionary
    timetable = {}
    timeslots = set()

    for r in rows:
        day = r["day"]
        time_range = f"{r['start_time']} - {r['end_time']}"
        # Store subject and class info
        timetable[(day, time_range)] = {
            "subject": r["subject_name"],
            "class": r["class_name"],
            "room": r["room_no"]
        }
        timeslots.add(time_range)

    # Sort timeslots by start time
    timeslots = sorted(list(timeslots))

    return render_template("teacher_dashboard.html",
                           name=session["name"],
                           timetable=timetable,
                           timeslots=timeslots)

# NOTE: Manual start_session route REMOVED
# Attendance is now fully automated via auto_scheduler.py
# The system watches the timetable and starts/stops camera automatically


@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/login")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get counts for dashboard
    students = cursor.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    teachers = cursor.execute("SELECT COUNT(*) FROM users WHERE role='teacher'").fetchone()[0]
    classes = cursor.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
    subjects = cursor.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
    
    conn.close()
    
    return render_template("admin_dashboard.html", 
                           name=session["name"],
                           students=students,
                           teachers=teachers,
                           classes=classes,
                           subjects=subjects)

# -------- ADMIN: ADD USER --------
@app.route("/admin/add_user", methods=["GET", "POST"])
def add_user():
    if session.get("role") != "admin":
        return redirect("/login")
    
    message = ""
    conn = get_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        class_id = request.form.get("class_id") or None
        
        try:
            cursor.execute("""
                INSERT INTO users (name, email, password, role, class_id) 
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, password, role, class_id))
            conn.commit()
            message = f"User '{name}' added successfully!"
        except:
            message = "Error: Email already exists!"
    
    # Get classes for dropdown
    classes = cursor.execute("SELECT id, class_name, room_no FROM classes").fetchall()
    conn.close()
    
    return render_template("add_user.html", message=message, classes=classes)

# -------- ADMIN: VIEW ALL USERS --------
@app.route("/admin/users")
def manage_users():
    if session.get("role") != "admin":
        return redirect("/login")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    users = cursor.execute("""
        SELECT users.id, users.name, users.email, users.role, 
               classes.class_name, classes.room_no
        FROM users
        LEFT JOIN classes ON users.class_id = classes.id
        ORDER BY users.role, users.name
    """).fetchall()
    
    conn.close()
    
    return render_template("admin_users.html", users=users)

# -------- ADMIN: EDIT USER --------
@app.route("/admin/edit_user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if session.get("role") != "admin":
        return redirect("/login")
    
    conn = get_connection()
    cursor = conn.cursor()
    message = ""
    
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        class_id = request.form.get("class_id") or None
        
        try:
            cursor.execute("""
                UPDATE users
                SET name=?, email=?, password=?, role=?, class_id=?
                WHERE id=?
            """, (name, email, password, role, class_id, user_id))
            conn.commit()
            message = "User updated successfully!"
        except:
            message = "Error: Email already exists!"
    
    user = cursor.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    classes = cursor.execute("SELECT id, class_name, room_no FROM classes").fetchall()
    conn.close()
    
    return render_template("edit_user.html", user=user, classes=classes, message=message)

# -------- ADMIN: DELETE USER --------
@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if session.get("role") != "admin":
        return redirect("/login")
    
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    
    return redirect("/admin/users")

# -------- ADMIN: ADD SUBJECT --------
@app.route("/admin/add_subject", methods=["GET", "POST"])
def add_subject():
    if session.get("role") != "admin":
        return redirect("/login")
    
    message = ""
    conn = get_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        subject = request.form["subject"]
        cursor.execute("INSERT INTO subjects (subject_name) VALUES (?)", (subject,))
        conn.commit()
        message = f"Subject '{subject}' added successfully!"
    
    # Get existing subjects
    subjects = cursor.execute("SELECT * FROM subjects ORDER BY subject_name").fetchall()
    conn.close()
    
    return render_template("add_subject.html", message=message, subjects=subjects)

# -------- ADMIN: ADD CLASS --------
@app.route("/admin/add_class", methods=["GET", "POST"])
def add_class():
    if session.get("role") != "admin":
        return redirect("/login")
    
    message = ""
    conn = get_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        class_name = request.form["class_name"]
        section = request.form["section"]
        cursor.execute("INSERT INTO classes (class_name, room_no) VALUES (?, ?)", (class_name, section))
        conn.commit()
        message = f"Class '{class_name} - {section}' added successfully!"
    
    # Get existing classes
    classes = cursor.execute("SELECT * FROM classes ORDER BY class_name").fetchall()
    conn.close()
    
    return render_template("add_class.html", message=message, classes=classes)

# -------- ADMIN: TIMETABLE MANAGER --------
@app.route("/admin/timetable", methods=["GET", "POST"])
def manage_timetable():
    if session.get("role") != "admin":
        return redirect("/login")
    
    message = ""
    conn = get_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        class_id = request.form["class_id"]
        subject_id = request.form["subject_id"]
        teacher_id = request.form["teacher_id"]
        day = request.form["day"]
        start = request.form["start"]
        end = request.form["end"]
        
        cursor.execute("""
            INSERT INTO timetable (class_id, subject_id, teacher_id, day, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (class_id, subject_id, teacher_id, day, start, end))
        conn.commit()
        message = "Timetable slot added successfully!"
    
    # Get data for dropdowns
    classes = cursor.execute("SELECT id, class_name, room_no FROM classes").fetchall()
    subjects = cursor.execute("SELECT id, subject_name FROM subjects").fetchall()
    teachers = cursor.execute("SELECT id, name FROM users WHERE role='teacher'").fetchall()
    
    # Get current timetable
    timetable = cursor.execute("""
        SELECT timetable.id, classes.class_name, subjects.subject_name, users.name as teacher,
               timetable.day, timetable.start_time, timetable.end_time
        FROM timetable
        JOIN classes ON timetable.class_id = classes.id
        JOIN subjects ON timetable.subject_id = subjects.id
        JOIN users ON timetable.teacher_id = users.id
        ORDER BY 
            CASE timetable.day 
                WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 
                WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 
            END,
            timetable.start_time
    """).fetchall()
    
    conn.close()
    
    return render_template("admin_timetable.html",
                           message=message,
                           classes=classes,
                           subjects=subjects,
                           teachers=teachers,
                           timetable=timetable)

# -------- ADMIN: DELETE TIMETABLE SLOT --------
@app.route("/admin/timetable/delete/<int:slot_id>", methods=["POST"])
def delete_timetable_slot(slot_id):
    if session.get("role") != "admin":
        return redirect("/login")
    
    conn = get_connection()
    conn.execute("DELETE FROM timetable WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()
    
    return redirect("/admin/timetable")

# -------- LIVE MONITOR (Public Dashboard) --------
@app.route("/")
def live_monitor():
    return render_template("live_monitor.html")

@app.route("/api/live")
def live_attendance():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, face_entry, face_exit, duration, status
        FROM live_attendance
        ORDER BY name
    """)

    rows = cursor.fetchall()
    conn.close()

    data = []
    for r in rows:
        data.append({
            "name": r["name"],
            "entry": r["face_entry"],
            "exit": r["face_exit"],
            "duration": r["duration"],
            "status": r["status"]
        })

    return jsonify(data)

# -------- TIMETABLE ROUTES --------
@app.route("/timetable")
def timetable():
    return render_template("timetable.html")

@app.route("/api/schedule", methods=["GET", "POST"])
def schedule_api():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        data = request.get_json()
        day = data["day"]
        hour = data["hour"]
        subject = data["subject"]

        if subject:
            # Insert or update the schedule entry
            cursor.execute("""
                INSERT OR REPLACE INTO schedule (day, hour, subject, start_time, end_time)
                VALUES (?, ?, ?, ?, ?)
            """, (day, hour, subject, "09:00", "10:00"))
        else:
            # If subject is empty, delete the entry
            cursor.execute("DELETE FROM schedule WHERE day = ? AND hour = ?", (day, hour))
        
        conn.commit()

    # Get all schedule entries
    cursor.execute("SELECT day, hour, subject FROM schedule ORDER BY day, hour")
    rows = cursor.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    # Make sure database exists
    if not os.path.exists(DB_PATH):
        print("Database not found. Run database_setup.py first.")
    app.run(debug=True)