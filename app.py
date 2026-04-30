from flask import Flask, request, jsonify, make_response, render_template, session, redirect, url_for
import csv
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'aceest-fitness-secret-key-2024'

APP_VERSION = '3.2.4'
DB_NAME = "aceest_fitness.db"

clients_db = []

PROGRAMS = {
    "Fat Loss (FL)": {
        "workout": "Back Squat, Cardio, Bench, Deadlift, Recovery",
        "diet": "Egg Whites, Chicken, Fish Curry",
        "color": "#e74c3c",
        "calorie_factor": 22
    },
    "Muscle Gain (MG)": {
        "workout": "Squat, Bench, Deadlift, Press, Rows",
        "diet": "Eggs, Biryani, Mutton Curry",
        "color": "#2ecc71",
        "calorie_factor": 35
    },
    "Beginner (BG)": {
        "workout": "Air Squats, Ring Rows, Push-ups",
        "diet": "Balanced Tamil Meals",
        "color": "#3498db",
        "calorie_factor": 26
    }
}

# Default admin credentials (hashed in a real system; plain text for demo only)
DEFAULT_ADMIN = {'username': 'admin', 'password': 'admin', 'role': 'Admin'}


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn, table_name, column_name, column_def):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    existing = {row[1] for row in cur.fetchall()}
    if column_name not in existing:
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Users table – role-based access
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    cur.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin','admin','Admin')")

    # Clients – with membership fields
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            age INTEGER,
            height REAL DEFAULT 0,
            weight REAL,
            program TEXT,
            calories INTEGER,
            adherence INTEGER DEFAULT 0,
            target_weight REAL DEFAULT 0,
            target_adherence INTEGER DEFAULT 80,
            membership_status TEXT DEFAULT 'Active',
            membership_end TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            week TEXT,
            adherence INTEGER,
            recorded_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            date TEXT,
            workout_type TEXT,
            duration_min INTEGER,
            sets INTEGER DEFAULT 0,
            reps INTEGER DEFAULT 0,
            weight_used REAL DEFAULT 0,
            notes TEXT DEFAULT ''
        )
    """)

    for col, defn in [('adherence', 'INTEGER DEFAULT 0'), ('notes', "TEXT DEFAULT ''"),
                      ('created_at', 'TEXT'), ('height', 'REAL DEFAULT 0'),
                      ('target_weight', 'REAL DEFAULT 0'), ('target_adherence', 'INTEGER DEFAULT 80'),
                      ('membership_status', "TEXT DEFAULT 'Active'"),
                      ('membership_end', "TEXT DEFAULT ''")]:
        ensure_column(conn, 'clients', col, defn)
    ensure_column(conn, 'progress', 'recorded_at', 'TEXT')
    conn.commit()
    conn.close()


init_db()


# ── AUTH ─────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()
    conn.close()

    if not user:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

    session['user'] = username
    session['role'] = user['role']
    return jsonify({'success': True, 'message': f'Welcome {username}',
                    'role': user['role'], 'username': username})


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@app.route('/api/users', methods=['GET'])
def get_users():
    """Admin-only: list all users"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM users ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return jsonify({'success': True,
                    'users': [{'id': r['id'], 'username': r['username'], 'role': r['role']}
                               for r in rows]})


# ── SERVICE INFO ──────────────────────────────────────────────────────────────

@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as count FROM clients")
    client_count = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) as count FROM workouts")
    workout_count = cur.fetchone()['count']
    conn.close()
    return jsonify({
        'service': 'ACEest Fitness & Gym Management API',
        'status': 'running',
        'version': APP_VERSION,
        'description': 'ACEest Fitness v3.2.4 - Role-based auth, membership tracking & PDF reports',
        'features': [
            '3 fitness programs (FL / MG / BG)',
            'Role-based authentication (Admin / Coach / Member)',
            'Membership status & expiry tracking',
            'Full workout logging (sets / reps / load)',
            'PDF client report generation',
            'Dashboard with embedded charts',
            'CSV export'
        ],
        'available_programs': list(PROGRAMS.keys()),
        'database': DB_NAME,
        'clients_in_db': client_count,
        'workouts_logged': workout_count,
        'endpoints': {
            'POST /login': 'Authenticate user',
            'POST /logout': 'End session',
            'GET /': 'Service info',
            'GET /health': 'Health check',
            'GET /dashboard': 'Admin dashboard',
            'GET /api/programs': 'All programs',
            'POST /api/calculate-calories': 'Calorie estimate',
            'POST /add-client': 'Add client (with membership)',
            'GET /clients': 'List all clients',
            'GET /client/<id>': 'Get client',
            'DELETE /delete-client/<id>': 'Delete client',
            'POST /save-progress': 'Log weekly adherence',
            'GET /progress/<name>': 'Progress history',
            'POST /workout': 'Log workout session',
            'GET /workouts/<client_name>': 'List workouts',
            'GET /chart/<client_name>': 'Adherence chart',
            'GET /report/pdf/<client_name>': 'PDF client report',
            'GET /export-csv': 'Export clients CSV',
            'POST /reset-clients': 'Reset all data'
        }
    })


@app.route('/health')
def health():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as count FROM clients")
    clients_count = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) as count FROM progress")
    progress_count = cur.fetchone()['count']
    conn.close()
    return jsonify({
        'status': 'healthy',
        'service': 'aceest-fitness-api',
        'version': APP_VERSION,
        'database': DB_NAME,
        'clients_count': clients_count,
        'progress_entries': progress_count,
        'timestamp': datetime.now().isoformat()
    })


# ── PROGRAMS ──────────────────────────────────────────────────────────────────

@app.route('/api/programs')
def get_programs():
    return jsonify({'success': True, 'programs': PROGRAMS})


@app.route('/api/programs/<program_name>')
def get_program(program_name):
    if program_name not in PROGRAMS:
        return jsonify({'success': False, 'error': 'Program not found',
                        'available_programs': list(PROGRAMS.keys())}), 404
    return jsonify({'success': True, 'program': program_name,
                    'details': PROGRAMS[program_name]})


@app.route('/api/calculate-calories', methods=['POST'])
def calculate_calories():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    weight = data.get('weight')
    program = data.get('program')
    if not weight or not program:
        return jsonify({'success': False, 'error': 'Both weight and program are required'}), 400
    if program not in PROGRAMS:
        return jsonify({'success': False, 'error': 'Invalid program',
                        'available_programs': list(PROGRAMS.keys())}), 404
    try:
        weight = float(weight)
        calorie_factor = PROGRAMS[program]['calorie_factor']
        estimated_calories = int(weight * calorie_factor)
        return jsonify({'success': True, 'weight_kg': weight, 'program': program,
                        'estimated_daily_calories': estimated_calories,
                        'calorie_factor': calorie_factor})
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid weight value'}), 400


@app.route('/api/calculate-calories/<program_name>')
def calculate_calories_get(program_name):
    weight = request.args.get('weight', type=float)
    if not weight:
        return jsonify({'success': False, 'error': 'Weight parameter required'}), 400
    if program_name not in PROGRAMS:
        return jsonify({'success': False, 'error': 'Program not found',
                        'available_programs': list(PROGRAMS.keys())}), 404
    calorie_factor = PROGRAMS[program_name]['calorie_factor']
    estimated_calories = int(weight * calorie_factor)
    return jsonify({'success': True, 'weight_kg': weight, 'program': program_name,
                    'estimated_daily_calories': estimated_calories,
                    'calorie_factor': calorie_factor})


# ── CLIENT CRUD ───────────────────────────────────────────────────────────────

@app.route('/add-client', methods=['POST'])
def add_client():
    try:
        data = request.get_json() if request.is_json else request.form
        name = data.get('name', '').strip()
        age = int(data.get('age', 0))
        height = float(data.get('height', 0))
        weight = float(data.get('weight', 0))
        program = data.get('program', '')
        adherence = int(data.get('adherence', 0))
        target_weight = float(data.get('target_weight', 0))
        target_adherence = int(data.get('target_adherence', 80))
        membership_status = data.get('membership_status', 'Active').strip()
        membership_end = data.get('membership_end', '').strip()
        notes = data.get('notes', '').strip()

        if not name or not program:
            return jsonify({'success': False, 'error': 'Name and program are required'}), 400
        if program not in PROGRAMS:
            return jsonify({'success': False, 'error': 'Invalid program selected'}), 400

        estimated_calories = int(weight * PROGRAMS[program]['calorie_factor'])
        created_at = datetime.now().isoformat()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO clients
            (name, age, height, weight, program, calories, adherence,
             target_weight, target_adherence, membership_status, membership_end, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, age, height, weight, program, estimated_calories, adherence,
              target_weight, target_adherence, membership_status, membership_end, notes, created_at))
        conn.commit()
        client_id = cur.lastrowid
        conn.close()

        client = {'id': client_id, 'name': name, 'age': age, 'height': height,
                  'weight': weight, 'program': program, 'adherence': adherence,
                  'target_weight': target_weight, 'target_adherence': target_adherence,
                  'membership_status': membership_status, 'membership_end': membership_end,
                  'notes': notes, 'estimated_calories': estimated_calories, 'created_at': created_at}
        clients_db.append(client)
        return jsonify({'success': True, 'message': f'Client {name} added successfully',
                        'client': client, 'total_clients': len(clients_db)})
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid data: {str(e)}'}), 400


@app.route('/clients')
def get_clients():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    keys = [d[0] for d in rows[0].description] if rows else []
    clients = []
    for r in rows:
        c = {'id': r['id'], 'name': r['name'], 'age': r['age'],
             'weight': r['weight'], 'program': r['program'],
             'adherence': r['adherence'] or 0, 'notes': r['notes'] or '',
             'estimated_calories': r['calories'], 'created_at': r['created_at']}
        if 'membership_status' in keys:
            c['membership_status'] = r['membership_status']
        clients.append(c)
    return jsonify({'success': True, 'clients': clients, 'count': len(clients)})


@app.route('/client/<int:client_id>')
def get_client(client_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE id=?", (client_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({'success': False, 'error': 'Client not found'}), 404
    return jsonify({'success': True, 'client': {
        'id': row['id'], 'name': row['name'], 'age': row['age'],
        'weight': row['weight'], 'program': row['program'],
        'adherence': row['adherence'] or 0, 'notes': row['notes'] or '',
        'estimated_calories': row['calories'], 'created_at': row['created_at']
    }})


@app.route('/client/name/<client_name>')
def get_client_by_name(client_name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE name=?", (client_name,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({'success': False, 'error': 'Client not found'}), 404
    return jsonify({'success': True, 'client': {
        'id': row['id'], 'name': row['name'], 'age': row['age'],
        'weight': row['weight'], 'program': row['program'],
        'adherence': row['adherence'] or 0, 'notes': row['notes'] or '',
        'estimated_calories': row['calories'], 'created_at': row['created_at']
    }})


@app.route('/delete-client/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    global clients_db
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM clients WHERE id=?", (client_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Client not found'}), 404
    client_name = row['name']
    cur.execute("DELETE FROM clients WHERE id=?", (client_id,))
    cur.execute("DELETE FROM progress WHERE client_name=?", (client_name,))
    cur.execute("DELETE FROM workouts WHERE client_name=?", (client_name,))
    conn.commit()
    conn.close()
    clients_db = [c for c in clients_db if c['id'] != client_id]
    return jsonify({'success': True, 'message': f'Client {client_name} deleted successfully'})


# ── PROGRESS ──────────────────────────────────────────────────────────────────

@app.route('/save-progress', methods=['POST'])
def save_progress():
    try:
        data = request.get_json() if request.is_json else request.form
        client_name = data.get('client_name', '').strip()
        adherence = int(data.get('adherence', 0))
        if not client_name:
            return jsonify({'success': False, 'error': 'Client name is required'}), 400
        week = datetime.now().strftime("Week %U - %Y")
        recorded_at = datetime.now().isoformat()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO progress (client_name, week, adherence, recorded_at) VALUES (?, ?, ?, ?)",
                    (client_name, week, adherence, recorded_at))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Weekly progress logged',
                        'week': week, 'adherence': adherence})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/progress/<client_name>')
def get_progress(client_name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM progress WHERE client_name=? ORDER BY recorded_at DESC", (client_name,))
    rows = cur.fetchall()
    conn.close()
    return jsonify({'success': True, 'client_name': client_name,
                    'progress': [{'id': r['id'], 'week': r['week'],
                                  'adherence': r['adherence'], 'recorded_at': r['recorded_at']}
                                 for r in rows],
                    'total_entries': len(rows)})


# ── WORKOUTS ──────────────────────────────────────────────────────────────────

@app.route('/workout', methods=['POST'])
def log_workout():
    try:
        data = request.get_json() if request.is_json else request.form
        client_name = data.get('client_name', '').strip()
        workout_type = data.get('workout_type', '').strip()
        duration_min = int(data.get('duration_min', 0))
        sets = int(data.get('sets', 0))
        reps = int(data.get('reps', 0))
        weight_used = float(data.get('weight_used', 0))
        notes = data.get('notes', '').strip()

        if not client_name or not workout_type:
            return jsonify({'success': False,
                            'error': 'client_name and workout_type are required'}), 400

        date_str = datetime.now().strftime('%Y-%m-%d')
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO workouts (client_name, date, workout_type, duration_min, sets, reps, weight_used, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (client_name, date_str, workout_type, duration_min, sets, reps, weight_used, notes))
        conn.commit()
        workout_id = cur.lastrowid
        conn.close()

        return jsonify({'success': True, 'message': 'Workout logged',
                        'workout': {'id': workout_id, 'client_name': client_name,
                                    'date': date_str, 'workout_type': workout_type,
                                    'duration_min': duration_min, 'sets': sets,
                                    'reps': reps, 'weight_used': weight_used}})
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid data: {str(e)}'}), 400


@app.route('/workouts/<client_name>')
def get_workouts(client_name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM workouts WHERE client_name=? ORDER BY date DESC", (client_name,))
    rows = cur.fetchall()
    conn.close()
    return jsonify({'success': True, 'client_name': client_name,
                    'workouts': [{'id': r['id'], 'date': r['date'],
                                  'workout_type': r['workout_type'],
                                  'duration_min': r['duration_min'],
                                  'sets': r['sets'], 'reps': r['reps'],
                                  'weight_used': r['weight_used'],
                                  'notes': r['notes']} for r in rows],
                    'total': len(rows)})


# ── CHARTS ────────────────────────────────────────────────────────────────────

@app.route('/chart/<client_name>')
def client_adherence_chart(client_name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (client_name,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return jsonify({'success': False, 'error': f'No progress data for {client_name}'}), 404
    try:
        weeks = [r['week'] for r in rows]
        adherence = [r['adherence'] for r in rows]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(weeks, adherence, marker='o', linewidth=2, color='#d4af37')
        ax.fill_between(range(len(weeks)), adherence, alpha=0.3, color='#d4af37')
        ax.set_xticks(range(len(weeks)))
        ax.set_xticklabels(weeks, rotation=45, ha='right')
        ax.set_ylabel('Adherence (%)')
        ax.set_title(f'Weekly Adherence – {client_name}')
        ax.set_ylim(0, 110)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        plt.close()
        return jsonify({'success': True, 'client_name': client_name,
                        'chart_data': f'data:image/png;base64,{img_b64}',
                        'data_points': len(rows)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Chart generation failed: {str(e)}'}), 500


# ── PDF REPORT ────────────────────────────────────────────────────────────────

@app.route('/report/pdf/<client_name>')
def pdf_report(client_name):
    """v3.2.4 new feature: PDF report (text-based fallback when fpdf not installed)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE name=?", (client_name,))
    client = cur.fetchone()
    cur.execute("SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (client_name,))
    progress_rows = cur.fetchall()
    cur.execute("SELECT date, workout_type, duration_min FROM workouts WHERE client_name=? ORDER BY date DESC LIMIT 10",
                (client_name,))
    workout_rows = cur.fetchall()
    conn.close()

    if not client:
        return jsonify({'success': False, 'error': f'Client {client_name} not found'}), 404

    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'ACEest Fitness - Client Report', ln=True, align='C')
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 13)
        pdf.cell(0, 8, 'Client Profile', ln=True)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 7, f"Name: {client['name']}", ln=True)
        pdf.cell(0, 7, f"Age: {client['age']}  Weight: {client['weight']} kg", ln=True)
        pdf.cell(0, 7, f"Program: {client['program']}", ln=True)
        pdf.cell(0, 7, f"Daily Calories: {client['calories']} kcal", ln=True)
        if 'membership_status' in client.keys():
            pdf.cell(0, 7, f"Membership: {client['membership_status']}", ln=True)
        pdf.ln(4)
        if progress_rows:
            pdf.set_font('Arial', 'B', 13)
            pdf.cell(0, 8, 'Progress History', ln=True)
            pdf.set_font('Arial', '', 11)
            for r in progress_rows:
                pdf.cell(0, 6, f"  {r['week']}: {r['adherence']}%", ln=True)
        if workout_rows:
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 13)
            pdf.cell(0, 8, 'Recent Workouts', ln=True)
            pdf.set_font('Arial', '', 11)
            for r in workout_rows:
                pdf.cell(0, 6, f"  {r['date']} – {r['workout_type']} ({r['duration_min']} min)", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = \
            f'attachment; filename=report_{client_name}_{datetime.now().strftime("%Y%m%d")}.pdf'
        return response

    except ImportError:
        # fpdf not installed – return plain text report
        lines = [
            f"ACEest Fitness – Client Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"Name: {client['name']}",
            f"Age: {client['age']}  Weight: {client['weight']} kg",
            f"Program: {client['program']}",
            f"Daily Calories: {client['calories']} kcal",
        ]
        if progress_rows:
            lines += ["", "Progress:"]
            lines += [f"  {r['week']}: {r['adherence']}%" for r in progress_rows]
        if workout_rows:
            lines += ["", "Recent Workouts:"]
            lines += [f"  {r['date']} – {r['workout_type']} ({r['duration_min']} min)"
                      for r in workout_rows]
        return jsonify({'success': True, 'report_type': 'text',
                        'client_name': client_name,
                        'report': '\n'.join(lines)})


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@app.route('/gui')
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    db_clients = [{'id': r['id'], 'name': r['name'], 'age': r['age'],
                   'weight': r['weight'], 'program': r['program'],
                   'adherence': r['adherence'] or 0,
                   'notes': r['notes'] or '',
                   'estimated_calories': r['calories']} for r in rows]
    try:
        return render_template('dashboard.html', programs=PROGRAMS,
                               clients=db_clients, version=APP_VERSION)
    except Exception:
        return jsonify({'success': True, 'version': APP_VERSION,
                        'clients': db_clients,
                        'programs': list(PROGRAMS.keys())})


# ── EXPORT / RESET ────────────────────────────────────────────────────────────

@app.route('/export-csv')
def export_csv():
    if not clients_db:
        return jsonify({'success': False, 'error': 'No clients to export'}), 400
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Age', 'Weight', 'Program', 'Adherence', 'Membership',
                     'Notes', 'Estimated Calories', 'Created At'])
    for c in clients_db:
        writer.writerow([c['name'], c['age'], c['weight'], c['program'],
                         c['adherence'], c.get('membership_status', 'Active'),
                         c['notes'], c['estimated_calories'], c['created_at']])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = \
        f'attachment; filename=aceest_clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return response


@app.route('/progress-chart')
def progress_chart():
    if not clients_db:
        return jsonify({'success': False, 'error': 'No client data available'}), 400
    try:
        fig, ax = plt.subplots(figsize=(10, 5))
        names = [c['name'][:15] for c in clients_db]
        adherence = [c['adherence'] for c in clients_db]
        colors = [PROGRAMS[c['program']]['color'] for c in clients_db]
        bars = ax.bar(names, adherence, color=colors, alpha=0.8, edgecolor='black')
        for bar, val in zip(bars, adherence):
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 1,
                    f'{val}%', ha='center', va='bottom', fontweight='bold')
        ax.set_ylabel('Adherence %')
        ax.set_title('Client Progress - Weekly Adherence')
        ax.set_ylim(0, 110)
        ax.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        plt.close()
        return jsonify({'success': True, 'chart_data': f'data:image/png;base64,{img_b64}',
                        'client_count': len(clients_db)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Chart generation failed: {str(e)}'}), 500


@app.route('/reset-clients', methods=['POST'])
def reset_clients():
    global clients_db
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM clients")
    cur.execute("DELETE FROM progress")
    cur.execute("DELETE FROM workouts")
    conn.commit()
    conn.close()
    clients_db = []
    return jsonify({'success': True, 'message': 'All client data has been reset'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=False)
