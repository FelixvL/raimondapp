from flask import Flask, render_template, request, redirect, session, send_from_directory, jsonify
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

load_dotenv()

app = Flask(__name__, template_folder='frontend/pages', static_folder='frontend/static')
app.secret_key = os.urandom(24)

# Database configuration
db_config = {
    'user': os.getenv('db_config_user'),
    'password': os.getenv('db_config_password'),
    'host': os.getenv('db_config_host'),
    'database': os.getenv('db_config_database')
}

# Parse users from environment variable
def get_users():
    users_str = os.getenv('USERS', '')
    users = {}
    for user in users_str.split(','):
        if ':' in user:
            username, password = user.split(':')
            users[username.lower()] = password
    return users

USERS = get_users()

# Route for the landing page
@app.route('/')
def landing_page():
    return render_template('index.html', username=session.get('username'))

# Route for the absence form
@app.route('/form')
def absence_form():
    return render_template('form.html')

# Route for processing the absence form
@app.route('/submit', methods=['POST'])
def submit_absence():
    student_id = request.form.get('student_id')
    was_aanwezig = request.form.get('was_aanwezig')
    datum = request.form.get('datum')
    reden = request.form.get('reden')

    # Check if required fields are present
    if not all([student_id, was_aanwezig, datum]):
        return "Missing form data", 400

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT name FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return "Student not found", 404

    student_name = student['name']
    query = "INSERT INTO absence_info (student_id, naam, was_aanwezig, datum, reden) VALUES (%s, %s, %s, %s, %s)"
    values = (student_id, student_name, was_aanwezig, datum, reden)  # reden can be None
    cursor.execute(query, values)

    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/view')

# Route for viewing absences
@app.route('/view')
def view_absences():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT students.name AS student_name, absence_info.was_aanwezig, absence_info.datum, absence_info.reden
        FROM absence_info
        JOIN students ON absence_info.student_id = students.id
        WHERE students.on_academy = TRUE
    """)
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view.html', absences=data)

# Route for searching absences by name
@app.route('/search', methods=['GET'])
def search():
    name = request.args.get('name', '')
    attendance = request.args.get('attendance', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT students.name, presentie_logs.status, presentie_logs.datum, presentie_logs.reason
        FROM presentie_logs
        JOIN students ON presentie_logs.student_id = students.id
        WHERE 1=1
    """
    params = []

    if name:
        query += " AND students.name LIKE %s"
        params.append(f"%{name}%")
    if attendance:
        query += " AND presentie_logs.status = %s"
        params.append(attendance)
    if start_date:
        query += " AND presentie_logs.datum >= %s"
        params.append(start_date)
    if end_date:
        query += " AND presentie_logs.datum <= %s"
        params.append(end_date)

    cursor.execute(query, params)
    absences = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('search.html', absences=absences)

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']

        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect('/')
        else:
            return redirect('/login?error=invalid_credentials')

    return render_template('login.html')

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect('/login')

# Protect routes
@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'logged_in' not in session:
        return redirect('/login')

    if 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        idle_time = datetime.now(pytz.UTC) - last_activity
        if idle_time > timedelta(minutes=30):
            session.clear()
            return redirect('/login?error=session_timeout')

    session['last_activity'] = datetime.now(pytz.UTC).isoformat()

# Ensure that static files are served correctly
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('frontend/static', filename)

# Endpoint to get all classes
@app.route('/api/classes', methods=['GET'])
def get_classes():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM classes")  # Adjust the query as needed
    classes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(classes)

# Endpoint to get students by class ID
@app.route('/api/class/<int:class_id>/students', methods=['GET'])
def get_students_by_class(class_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM students WHERE class_id = %s", (class_id,))
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'students': students})

# Route for adding a new student
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form.get('name')
        class_id = request.form.get('class_id')

        # Check if required fields are present
        if not all([name, class_id]):
            return "Missing form data", 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Insert the new student into the database
        cursor.execute("""
            INSERT INTO students (name, class_id) 
            VALUES (%s, %s)
        """, (name, class_id))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect('/view')  # Redirect to the view page after adding

    # If GET request, fetch classes to display in the form
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM classes")
    classes = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('add_student.html', classes=classes)

# Route for viewing a student's profile
@app.route('/personview/<int:student_id>')
def person_view(student_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Fetch student information along with class name
    cursor.execute("""
        SELECT students.*, classes.name AS class_name 
        FROM students 
        JOIN classes ON students.class_id = classes.id 
        WHERE students.id = %s
    """, (student_id,))
    student = cursor.fetchone()

    if not student:
        return "Student not found", 404

    # Fetch attendance logs for the specific student from the absence_info table
    cursor.execute("""
        SELECT naam, was_aanwezig, datum, reden 
        FROM absence_info 
        WHERE student_id = %s
    """, (student_id,))
    presentie_logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('personview.html', student=student, presentie_logs=presentie_logs)

# Route to update academy status
@app.route('/update_academy_status/<int:student_id>', methods=['POST'])
def update_academy_status(student_id):
    data = request.get_json()
    is_on_academy = data.get('is_on_academy')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Update the student's academy status in the database
    cursor.execute("""
        UPDATE students 
        SET on_academy = %s 
        WHERE id = %s
    """, (1 if is_on_academy else 0, student_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)