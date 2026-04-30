from flask import Flask, request, jsonify, make_response
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

APP_VERSION = '1.0'
DB_NAME = "aceest_fitness.db"

# In-memory client store (backward compat for tests)
clients_db = []

PROGRAMS = {
    "Fat Loss (FL)": {
        "workout": "Mon: 5x5 Back Squat + AMRAP\nTue: EMOM 20min Assault Bike\nWed: Bench Press + 21-15-9\nThu: 10RFT Deadlifts/Box Jumps\nFri: 30min Active Recovery",
        "diet": "Breakfast: 3 Egg Whites + Oats Idli\nLunch: Grilled Chicken + Brown Rice\nDinner: Fish Curry + Millet Roti\nTarget: 2,000 kcal",
        "color": "#e74c3c",
        "calorie_factor": 22
    },
    "Muscle Gain (MG)": {
        "workout": "Mon: Squat 5x5\nTue: Bench 5x5\nWed: Deadlift 4x6\nThu: Front Squat 4x8\nFri: Incline Press 4x10\nSat: Barbell Rows 4x10",
        "diet": "Breakfast: 4 Eggs + PB Oats\nLunch: Chicken Biryani (250g Chicken)\nDinner: Mutton Curry + Jeera Rice\nTarget: 3,200 kcal",
        "color": "#2ecc71",
        "calorie_factor": 35
    },
    "Beginner (BG)": {
        "workout": "Circuit Training: Air Squats, Ring Rows, Push-ups.\nFocus: Technique Mastery & Form (90% Threshold)",
        "diet": "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati.\nProtein: 120g/day",
        "color": "#3498db",
        "calorie_factor": 26
    }
}


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            age INTEGER,
            weight REAL,
            program TEXT,
            calories INTEGER,
            adherence INTEGER DEFAULT 0,
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
    conn.commit()
    conn.close()


init_db()


@app.route('/')
def home():
    return jsonify({
        'service': 'ACEest Fitness & Gym Management API',
        'status': 'running',
        'version': APP_VERSION,
        'description': 'ACEest Fitness v1.0 - Program display: Fat Loss, Muscle Gain, Beginner',
        'features': [
            '3 fitness programs (FL / MG / BG)',
            'Weekly workout plans',
            'Daily nutrition plans (Tamil Nadu context)'
        ],
        'available_programs': list(PROGRAMS.keys()),
        'endpoints': {
            'GET /': 'Service info',
            'GET /health': 'Health check',
            'GET /api/programs': 'All programs',
            'GET /api/programs/<name>': 'Specific program',
            'POST /api/calculate-calories': 'Calorie estimate',
            'GET /api/calculate-calories/<program>?weight=X': 'Calorie estimate (GET)',
            'POST /add-client': 'Add client',
            'GET /clients': 'List clients',
            'GET /client/<id>': 'Get client',
            'DELETE /delete-client/<id>': 'Delete client',
            'POST /save-progress': 'Log weekly adherence',
            'GET /progress/<name>': 'Progress history',
            'GET /export-csv': 'Export clients CSV',
            'POST /reset-clients': 'Reset all data'
        }
    })


@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'aceest-fitness-api',
        'version': APP_VERSION,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/programs')
def get_programs():
    return jsonify({'success': True, 'programs': PROGRAMS})


@app.route('/api/programs/<program_name>')
def get_program(program_name):
    if program_name not in PROGRAMS:
        return jsonify({
            'success': False,
            'error': 'Program not found',
            'available_programs': list(PROGRAMS.keys())
        }), 404
    return jsonify({
        'success': True,
        'program': program_name,
        'details': PROGRAMS[program_name]
    })


@app.route('/api/calculate-calories', methods=['POST'])
def calculate_calories():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    weight = data.get('weight')
    program = data.get('program')

    if not weight or not program:
        return jsonify({
            'success': False,
            'error': 'Both weight and program are required'
        }), 400

    if program not in PROGRAMS:
        return jsonify({'success': False, 'error': 'Invalid program',
                        'available_programs': list(PROGRAMS.keys())}), 404

    try:
        weight = float(weight)
        calorie_factor = PROGRAMS[program]['calorie_factor']
        estimated_calories = int(weight * calorie_factor)
        return jsonify({
            'success': True,
            'weight_kg': weight,
            'program': program,
            'estimated_daily_calories': estimated_calories,
            'calorie_factor': calorie_factor
        })
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
    return jsonify({
        'success': True,
        'weight_kg': weight,
        'program': program_name,
        'estimated_daily_calories': estimated_calories,
        'calorie_factor': calorie_factor
    })


@app.route('/add-client', methods=['POST'])
def add_client():
    try:
        data = request.get_json() if request.is_json else request.form
        name = data.get('name', '').strip()
        age = int(data.get('age', 0))
        weight = float(data.get('weight', 0))
        program = data.get('program', '')
        adherence = int(data.get('adherence', 0))
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
            INSERT OR REPLACE INTO clients (name, age, weight, program, calories, adherence, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, age, weight, program, estimated_calories, adherence, notes, created_at))
        conn.commit()
        client_id = cur.lastrowid
        conn.close()

        client = {
            'id': client_id,
            'name': name,
            'age': age,
            'weight': weight,
            'program': program,
            'adherence': adherence,
            'notes': notes,
            'estimated_calories': estimated_calories,
            'created_at': created_at
        }
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
    clients = [{'id': r['id'], 'name': r['name'], 'age': r['age'], 'weight': r['weight'],
                 'program': r['program'], 'adherence': r['adherence'] or 0,
                 'notes': r['notes'] or '', 'estimated_calories': r['calories'],
                 'created_at': r['created_at']} for r in rows]
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
    conn.commit()
    conn.close()
    clients_db = [c for c in clients_db if c['id'] != client_id]
    return jsonify({'success': True, 'message': f'Client {client_name} deleted successfully'})


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


@app.route('/export-csv')
def export_csv():
    if not clients_db:
        return jsonify({'success': False, 'error': 'No clients to export'}), 400
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Age', 'Weight', 'Program', 'Adherence', 'Notes', 'Estimated Calories', 'Created At'])
    for c in clients_db:
        writer.writerow([c['name'], c['age'], c['weight'], c['program'],
                         c['adherence'], c['notes'], c['estimated_calories'], c['created_at']])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = \
        f'attachment; filename=aceest_clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return response


@app.route('/reset-clients', methods=['POST'])
def reset_clients():
    global clients_db
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM clients")
    cur.execute("DELETE FROM progress")
    conn.commit()
    conn.close()
    clients_db = []
    return jsonify({'success': True, 'message': 'All client data has been reset'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=False)
