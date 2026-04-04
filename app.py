
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, make_response
import json
import csv
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'aceest-fitness-secret-key-2024'

# Database configuration (from Aceestver2.0.1)
DB_NAME = "aceest_fitness.db"

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables (from Aceestver2.0.1)"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Clients table
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

    # Progress tracking table (from Aceestver2.0.1)
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

# Initialize database on startup
init_db()

# In-memory cache (for backward compatibility)
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

# ============== WEB INTERFACE ROUTES ==============

@app.route('/dashboard')
@app.route('/gui')
def dashboard():
    """Main web dashboard (GUI equivalent)"""
    return render_template('dashboard.html',
                         programs=PROGRAMS,
                         clients=clients_db)

@app.route('/add-client', methods=['POST'])
def add_client():
    """Add a new client (equivalent to save_client in GUI) - Now with SQLite from Aceestver2.0.1"""
    try:
        data = request.get_json() if request.is_json else request.form

        name = data.get('name', '').strip()
        age = int(data.get('age', 0))
        weight = float(data.get('weight', 0))
        program = data.get('program', '')
        adherence = int(data.get('adherence', 0))
        notes = data.get('notes', '').strip()

        if not name or not program:
            return jsonify({
                'success': False,
                'error': 'Name and program are required'
            }), 400

        if program not in PROGRAMS:
            return jsonify({
                'success': False,
                'error': 'Invalid program selected'
            }), 400

        estimated_calories = int(weight * PROGRAMS[program]['calorie_factor'])
        created_at = datetime.now().isoformat()

        # Save to SQLite database (from Aceestver2.0.1)
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT OR REPLACE INTO clients 
                (name, age, weight, program, calories, adherence, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, age, weight, program, estimated_calories, adherence, notes, created_at))
            conn.commit()
            client_id = cur.lastrowid
        except Exception as e:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Database error: {str(e)}'
            }), 500

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

        # Also update in-memory cache for backward compatibility
        clients_db.append(client)

        return jsonify({
            'success': True,
            'message': f'Client {name} added successfully',
            'client': client,
            'total_clients': len(clients_db)
        })

    except (ValueError, TypeError) as e:
        return jsonify({
            'success': False,
            'error': f'Invalid data: {str(e)}'
        }), 400

@app.route('/clients')
def get_clients():
    """Get all clients from SQLite database (from Aceestver2.0.1)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    clients = []
    for row in rows:
        clients.append({
            'id': row['id'],
            'name': row['name'],
            'age': row['age'],
            'weight': row['weight'],
            'program': row['program'],
            'adherence': row['adherence'] or 0,
            'notes': row['notes'] or '',
            'estimated_calories': row['calories'],
            'created_at': row['created_at']
        })

    return jsonify({
        'success': True,
        'clients': clients,
        'count': len(clients)
    })

@app.route('/client/<int:client_id>')
def get_client(client_id):
    """Get specific client details from SQLite (equivalent to load_client in Aceestver2.0.1)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE id=?", (client_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({
            'success': False,
            'error': 'Client not found'
        }), 404

    client = {
        'id': row['id'],
        'name': row['name'],
        'age': row['age'],
        'weight': row['weight'],
        'program': row['program'],
        'adherence': row['adherence'] or 0,
        'notes': row['notes'] or '',
        'estimated_calories': row['calories'],
        'created_at': row['created_at']
    }

    return jsonify({
        'success': True,
        'client': client
    })

@app.route('/client/name/<client_name>')
def get_client_by_name(client_name):
    """Get client by name from SQLite (equivalent to load_client in Aceestver2.0.1)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE name=?", (client_name,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({
            'success': False,
            'error': 'Client not found'
        }), 404

    client = {
        'id': row['id'],
        'name': row['name'],
        'age': row['age'],
        'weight': row['weight'],
        'program': row['program'],
        'adherence': row['adherence'] or 0,
        'notes': row['notes'] or '',
        'estimated_calories': row['calories'],
        'created_at': row['created_at']
    }

    return jsonify({
        'success': True,
        'client': client
    })

@app.route('/delete-client/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Delete client from SQLite database"""
    global clients_db

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM clients WHERE id=?", (client_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({
            'success': False,
            'error': 'Client not found'
        }), 404

    client_name = row['name']
    cur.execute("DELETE FROM clients WHERE id=?", (client_id,))
    # Also delete related progress records
    cur.execute("DELETE FROM progress WHERE client_name=?", (client_name,))
    conn.commit()
    conn.close()

    # Update in-memory cache
    clients_db = [c for c in clients_db if c['id'] != client_id]

    return jsonify({
        'success': True,
        'message': f'Client {client_name} deleted successfully'
    })

# ============== PROGRESS TRACKING (from Aceestver2.0.1) ==============

@app.route('/save-progress', methods=['POST'])
def save_progress():
    """Save weekly progress (equivalent to save_progress in Aceestver2.0.1)"""
    try:
        data = request.get_json() if request.is_json else request.form

        client_name = data.get('client_name', '').strip()
        adherence = int(data.get('adherence', 0))

        if not client_name:
            return jsonify({
                'success': False,
                'error': 'Client name is required'
            }), 400

        week = datetime.now().strftime("Week %U - %Y")
        recorded_at = datetime.now().isoformat()

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO progress (client_name, week, adherence, recorded_at)
            VALUES (?, ?, ?, ?)
        """, (client_name, week, adherence, recorded_at))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Weekly progress logged',
            'week': week,
            'adherence': adherence
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error saving progress: {str(e)}'
        }), 500

@app.route('/progress/<client_name>')
def get_progress(client_name):
    """Get progress history for a client"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM progress 
        WHERE client_name=? 
        ORDER BY recorded_at DESC
    """, (client_name,))
    rows = cur.fetchall()
    conn.close()

    progress_history = []
    for row in rows:
        progress_history.append({
            'id': row['id'],
            'week': row['week'],
            'adherence': row['adherence'],
            'recorded_at': row['recorded_at']
        })

    return jsonify({
        'success': True,
        'client_name': client_name,
        'progress': progress_history,
        'total_entries': len(progress_history)
    })

@app.route('/export-csv')
def export_csv():
    """Export clients to CSV (equivalent to GUI export function)"""
    if not clients_db:
        return jsonify({
            'success': False,
            'error': 'No clients to export'
        }), 400

    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Name', 'Age', 'Weight', 'Program', 'Adherence', 'Notes', 'Estimated Calories', 'Created At'])

    # Write client data
    for client in clients_db:
        writer.writerow([
            client['name'],
            client['age'],
            client['weight'],
            client['program'],
            client['adherence'],
            client['notes'],
            client['estimated_calories'],
            client['created_at']
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=aceest_clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    return response

@app.route('/progress-chart')
def progress_chart():
    if not clients_db:
        return jsonify({
            'success': False,
            'error': 'No client data available'
        })

    try:
        fig, ax = plt.subplots(figsize=(10, 6))

        names = [client['name'][:15] for client in clients_db]  # Limit name length
        adherence = [client['adherence'] for client in clients_db]

        colors = [PROGRAMS[client['program']]['color'] for client in clients_db]

        bars = ax.bar(names, adherence, color=colors, alpha=0.8, edgecolor='black', linewidth=1)

        ax.set_ylabel('Adherence %', fontsize=12, fontweight='bold')
        ax.set_title('Client Progress - Weekly Adherence', fontsize=14, fontweight='bold', pad=20)
        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        for bar, value in zip(bars, adherence):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{value}%', ha='center', va='bottom', fontweight='bold')

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)

        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()

        return jsonify({
            'success': True,
            'chart_data': f'data:image/png;base64,{img_base64}',
            'client_count': len(clients_db)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Chart generation failed: {str(e)}'
        }), 500

@app.route('/reset-clients', methods=['POST'])
def reset_clients():
    """Reset all client data in SQLite database"""
    global clients_db

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM clients")
    cur.execute("DELETE FROM progress")
    conn.commit()
    conn.close()

    clients_db = []

    return jsonify({
        'success': True,
        'message': 'All client data has been reset'
    })

# ============== API ROUTES (EXISTING) ==============

@app.route('/')
def home():
    return jsonify({
        'service': 'ACEest Fitness & Gym Management API',
        'status': 'running',
        'version': '2.0.1',
        'description': 'DevOps Assignment - Flask App with SQLite Database (based on Aceestver2.0.1)',
        'features': [
            'SQLite database persistence',
            'Progress tracking',
            'Client management'
        ],
        'available_programs': list(PROGRAMS.keys()),
        'endpoints': {
            'GET /': 'Service information',
            'GET /health': 'Health check',
            'GET /dashboard': 'Web GUI interface',
            'GET /api/programs': 'List all fitness programs',
            'GET /api/programs/<name>': 'Get specific program details',
            'POST /api/calculate-calories': 'Calculate calories for a program',
            'POST /add-client': 'Add new client (saved to SQLite)',
            'GET /clients': 'Get all clients from database',
            'GET /client/<id>': 'Get client by ID',
            'GET /client/name/<name>': 'Get client by name',
            'DELETE /delete-client/<id>': 'Delete a client',
            'POST /save-progress': 'Save weekly progress',
            'GET /progress/<name>': 'Get progress history',
            'GET /export-csv': 'Export clients to CSV',
            'GET /progress-chart': 'Generate progress chart',
            'POST /reset-clients': 'Reset all data'
        },
        'database': DB_NAME
    })

@app.route('/health')
def health():
    # Get client count from database
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
        'version': '2.0.1',
        'database': DB_NAME,
        'clients_count': clients_count,
        'progress_entries': progress_count,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/programs')
def get_programs():
    return jsonify({
        'success': True,
        'programs': PROGRAMS
    })

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
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400

    weight = data.get('weight')
    program = data.get('program')

    if not weight or not program:
        return jsonify({
            'success': False,
            'error': 'Both weight and program are required',
            'example': {'weight': 70, 'program': 'Fat Loss (FL)'}
        }), 400

    if program not in PROGRAMS:
        return jsonify({
            'success': False,
            'error': 'Invalid program',
            'available_programs': list(PROGRAMS.keys())
        }), 404

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
        return jsonify({
            'success': False,
            'error': 'Invalid weight value'
        }), 400

@app.route('/api/calculate-calories/<program_name>')
def calculate_calories_get(program_name):
    weight = request.args.get('weight', type=float)

    if not weight:
        return jsonify({
            'success': False,
            'error': 'Weight parameter required',
            'example': f'/api/calculate-calories/{program_name}?weight=70'
        }), 400

    if program_name not in PROGRAMS:
        return jsonify({
            'success': False,
            'error': 'Program not found',
            'available_programs': list(PROGRAMS.keys())
        }), 404

    calorie_factor = PROGRAMS[program_name]['calorie_factor']
    estimated_calories = int(weight * calorie_factor)

    return jsonify({
        'success': True,
        'weight_kg': weight,
        'program': program_name,
        'estimated_daily_calories': estimated_calories,
        'calorie_factor': calorie_factor
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9000, use_reloader=False)
