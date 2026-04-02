
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

app = Flask(__name__)
app.secret_key = 'aceest-fitness-secret-key-2024'

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
    """Add a new client (equivalent to save_client in GUI)"""
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

        client = {
            'id': len(clients_db) + 1,
            'name': name,
            'age': age,
            'weight': weight,
            'program': program,
            'adherence': adherence,
            'notes': notes,
            'estimated_calories': estimated_calories,
            'created_at': datetime.now().isoformat()
        }

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
    """Get all clients (for table display)"""
    return jsonify({
        'success': True,
        'clients': clients_db,
        'count': len(clients_db)
    })

@app.route('/client/<int:client_id>')
def get_client(client_id):
    """Get specific client details"""
    client = next((c for c in clients_db if c['id'] == client_id), None)
    if not client:
        return jsonify({
            'success': False,
            'error': 'Client not found'
        }), 404

    return jsonify({
        'success': True,
        'client': client
    })

@app.route('/delete-client/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    global clients_db
    client = next((c for c in clients_db if c['id'] == client_id), None)
    if not client:
        return jsonify({
            'success': False,
            'error': 'Client not found'
        }), 404

    clients_db = [c for c in clients_db if c['id'] != client_id]

    return jsonify({
        'success': True,
        'message': f'Client {client["name"]} deleted successfully'
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
    global clients_db
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
        'version': '2.0.0',
        'description': 'DevOps Assignment - Complete Web Application with GUI equivalent',
        'available_programs': list(PROGRAMS.keys()),
        'endpoints': {
            'GET /': 'Service information',
            'GET /health': 'Health check',
            'GET /dashboard': 'Web GUI interface',
            'GET /api/programs': 'List all fitness programs',
            'GET /api/programs/<name>': 'Get specific program details',
            'POST /api/calculate-calories': 'Calculate calories for a program',
            'POST /add-client': 'Add new client',
            'GET /clients': 'Get all clients',
            'GET /export-csv': 'Export clients to CSV',
            'GET /progress-chart': 'Generate progress chart'
        },
        'total_clients': len(clients_db)
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'aceest-fitness-api',
        'clients_count': len(clients_db),
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
