from flask import Flask, render_template, jsonify, request, redirect, session, url_for, send_file
import sqlite3
import os
import subprocess
import openpyxl
from io import BytesIO
from datetime import date

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
    rfid_status = ""
    conn = get_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        class_id = request.form.get("class_id") or None
        
        rfid_uid = None
        
        # ONLY capture RFID if user is a STUDENT
        if role == "student":
            cursor.execute("SELECT uid FROM rfid_buffer LIMIT 1")
            rfid_result = cursor.fetchone()
            if rfid_result:
                rfid_uid = rfid_result["uid"]
                # Clear buffer after use
                cursor.execute("DELETE FROM rfid_buffer")
        
        try:
            cursor.execute("""
                INSERT INTO users (name, email, password, role, class_id, rfid_uid) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, email, password, role, class_id, rfid_uid))
            conn.commit()
            
            if role == "student":
                if rfid_uid:
                    message = f"Student '{name}' added with RFID card!"
                else:
                    message = f"Student '{name}' added (⚠️ No RFID card - tap card and try again)"
            else:
                message = f"Teacher '{name}' added successfully!"
        except:
            message = "Error: Email already exists!"
    
    # Check if there's a card in the buffer (for students)
    cursor.execute("SELECT uid FROM rfid_buffer LIMIT 1")
    buffered_card = cursor.fetchone()
    if buffered_card:
        rfid_status = f"Card ready: {buffered_card['uid']}"
    
    # Get classes for dropdown
    classes = cursor.execute("SELECT id, class_name, room_no FROM classes").fetchall()
    conn.close()
    
    return render_template("add_user.html", message=message, classes=classes, rfid_status=rfid_status)

# -------- ADMIN: VIEW ALL USERS --------
@app.route("/admin/users")
def manage_users():
    if session.get("role") != "admin":
        return redirect("/login")
    
    role_filter = request.args.get("role", "all")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Base query - exclude admin accounts
    query = """
        SELECT users.id, users.name, users.email, users.role, 
               classes.class_name, classes.room_no, users.rfid_uid
        FROM users
        LEFT JOIN classes ON users.class_id = classes.id
        WHERE users.role != 'admin'
    """
    
    params = []
    
    # Apply role filter if specified
    if role_filter in ["student", "teacher"]:
        query += " AND users.role = ?"
        params.append(role_filter)
    
    query += " ORDER BY users.role, users.name"
    
    users = cursor.execute(query, params).fetchall()
    conn.close()
    
    return render_template("admin_users.html", users=users, role_filter=role_filter)

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

# -------- TEACHER: DOWNLOAD REPORT --------
@app.route("/teacher/download_report")
def teacher_download_report():
    if session.get("role") != "teacher":
        return redirect("/login")
    
    teacher_id = session["user_id"]
    today = date.today().isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get attendance for subjects taught by this teacher
    cursor.execute("""
        SELECT DISTINCT users.name as student_name, subjects.subject_name, 
               attendance.date, attendance.status
        FROM attendance
        JOIN users ON attendance.student_id = users.id
        JOIN subjects ON attendance.subject_id = subjects.id
        JOIN timetable ON timetable.subject_id = subjects.id
        WHERE timetable.teacher_id = ? AND attendance.date = ?
        ORDER BY subjects.subject_name, users.name
    """, (teacher_id, today))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance"
    
    # Header styling
    ws.append(["Student Name", "Subject", "Date", "Status"])
    
    for r in rows:
        ws.append([r["student_name"], r["subject_name"], r["date"], r["status"]])
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column_letter].width = max_length + 2
    
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    
    return send_file(
        file_stream,
        download_name=f"Teacher_Attendance_{today}.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -------- ADMIN: DOWNLOAD REPORT --------
@app.route("/admin/download_report", methods=["GET", "POST"])
def admin_download_report():
    if session.get("role") != "admin":
        return redirect("/login")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        class_id = request.form["class_id"]
        selected_date = request.form["date"]
        
        # Get class name for filename
        cursor.execute("SELECT class_name FROM classes WHERE id = ?", (class_id,))
        class_info = cursor.fetchone()
        class_name = class_info["class_name"] if class_info else "Unknown"
        
        # Get attendance for selected class and date
        cursor.execute("""
            SELECT users.name as student_name, subjects.subject_name, 
                   attendance.date, attendance.status
            FROM attendance
            JOIN users ON attendance.student_id = users.id
            JOIN subjects ON attendance.subject_id = subjects.id
            WHERE users.class_id = ? AND attendance.date = ?
            ORDER BY subjects.subject_name, users.name
        """, (class_id, selected_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Create Excel workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Attendance"
        
        # Add header info
        ws.append([f"Class: {class_name}"])
        ws.append([f"Date: {selected_date}"])
        ws.append([])  # Empty row
        ws.append(["Student Name", "Subject", "Date", "Status"])
        
        for r in rows:
            ws.append([r["student_name"], r["subject_name"], r["date"], r["status"]])
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            ws.column_dimensions[column_letter].width = max_length + 2
        
        file_stream = BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)
        
        safe_class_name = class_name.replace(" ", "_")
        return send_file(
            file_stream,
            download_name=f"{safe_class_name}_Attendance_{selected_date}.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # GET request - show form
    classes = cursor.execute("SELECT id, class_name, room_no FROM classes").fetchall()
    conn.close()
    
    return render_template("admin_download.html", classes=classes)

if __name__ == "__main__":
    # Make sure database exists
    if not os.path.exists(DB_PATH):
        print("Database not found. Run database_setup.py first.")
    app.run(debug=True)