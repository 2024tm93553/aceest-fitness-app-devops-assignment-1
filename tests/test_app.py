"""
ACEest Fitness App - Comprehensive Unit Tests
Tests for Flask application endpoints and business logic
"""

import pytest
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from app import app, PROGRAMS


# ==================== FIXTURES ====================

@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    # Reset clients before each test
    app_module.clients_db.clear()
    with app.test_client() as test_client:
        yield test_client
    # Cleanup after test
    app_module.clients_db.clear()


@pytest.fixture
def reset_clients():
    """Reset clients database before each test"""
    app_module.clients_db.clear()
    yield
    app_module.clients_db.clear()


@pytest.fixture
def sample_client_data():
    """Sample client data for testing"""
    return {
        'name': 'Test User',
        'age': 25,
        'weight': 70,
        'program': 'Fat Loss (FL)',
        'adherence': 80,
        'notes': 'Test notes'
    }


# ==================== HEALTH & HOME ENDPOINT TESTS ====================

class TestHealthEndpoint:
    """Tests for /health endpoint"""

    def test_health_returns_200(self, client):
        """Test that health endpoint returns 200 OK"""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """Test that health endpoint returns healthy status"""
        response = client.get('/health')
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    def test_health_returns_service_name(self, client):
        """Test that health endpoint returns correct service name"""
        response = client.get('/health')
        data = json.loads(response.data)
        assert data['service'] == 'aceest-fitness-api'

    def test_health_contains_timestamp(self, client):
        """Test that health endpoint returns a timestamp"""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'timestamp' in data


class TestHomeEndpoint:
    """Tests for / (home) endpoint"""

    def test_home_returns_200(self, client):
        """Test that home endpoint returns 200 OK"""
        response = client.get('/')
        assert response.status_code == 200

    def test_home_returns_service_info(self, client):
        """Test that home endpoint returns service information"""
        response = client.get('/')
        data = json.loads(response.data)
        assert data['service'] == 'ACEest Fitness & Gym Management API'
        assert data['status'] == 'running'

    def test_home_lists_available_programs(self, client):
        """Test that home endpoint lists all available programs"""
        response = client.get('/')
        data = json.loads(response.data)
        assert 'available_programs' in data
        assert len(data['available_programs']) == 3


# ==================== PROGRAMS API TESTS ====================

class TestProgramsAPI:
    """Tests for /api/programs endpoints"""

    def test_get_all_programs(self, client):
        """Test getting all fitness programs"""
        response = client.get('/api/programs')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'programs' in data

    def test_programs_contain_required_keys(self, client):
        """Test that each program has required attributes"""
        response = client.get('/api/programs')
        data = json.loads(response.data)

        for program_name, program_data in data['programs'].items():
            assert 'workout' in program_data
            assert 'diet' in program_data
            assert 'calorie_factor' in program_data

    def test_get_specific_program_fat_loss(self, client):
        """Test getting Fat Loss program details"""
        response = client.get('/api/programs/Fat Loss (FL)')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['program'] == 'Fat Loss (FL)'

    def test_get_specific_program_muscle_gain(self, client):
        """Test getting Muscle Gain program details"""
        response = client.get('/api/programs/Muscle Gain (MG)')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['details']['calorie_factor'] == 35

    def test_get_invalid_program_returns_404(self, client):
        """Test that invalid program returns 404"""
        response = client.get('/api/programs/Invalid Program')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False


# ==================== CALORIE CALCULATION TESTS ====================

class TestCalorieCalculation:
    """Tests for calorie calculation logic"""

    def test_calculate_calories_fat_loss(self, client):
        """Test calorie calculation for Fat Loss program"""
        response = client.post('/api/calculate-calories',
                              data=json.dumps({'weight': 70, 'program': 'Fat Loss (FL)'}),
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Fat Loss factor = 22, so 70 * 22 = 1540
        assert data['estimated_daily_calories'] == 1540

    def test_calculate_calories_muscle_gain(self, client):
        """Test calorie calculation for Muscle Gain program"""
        response = client.post('/api/calculate-calories',
                              data=json.dumps({'weight': 80, 'program': 'Muscle Gain (MG)'}),
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Muscle Gain factor = 35, so 80 * 35 = 2800
        assert data['estimated_daily_calories'] == 2800

    def test_calculate_calories_beginner(self, client):
        """Test calorie calculation for Beginner program"""
        response = client.post('/api/calculate-calories',
                              data=json.dumps({'weight': 65, 'program': 'Beginner (BG)'}),
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Beginner factor = 26, so 65 * 26 = 1690
        assert data['estimated_daily_calories'] == 1690

    def test_calculate_calories_missing_weight(self, client):
        """Test that missing weight returns error"""
        response = client.post('/api/calculate-calories',
                              data=json.dumps({'program': 'Fat Loss (FL)'}),
                              content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False

    def test_calculate_calories_missing_program(self, client):
        """Test that missing program returns error"""
        response = client.post('/api/calculate-calories',
                              data=json.dumps({'weight': 70}),
                              content_type='application/json')
        assert response.status_code == 400

    def test_calculate_calories_invalid_program(self, client):
        """Test that invalid program returns error"""
        response = client.post('/api/calculate-calories',
                              data=json.dumps({'weight': 70, 'program': 'Invalid'}),
                              content_type='application/json')
        assert response.status_code == 404

    def test_calculate_calories_get_method(self, client):
        """Test calorie calculation via GET method"""
        response = client.get('/api/calculate-calories/Fat Loss (FL)?weight=70')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['estimated_daily_calories'] == 1540


# ==================== CLIENT MANAGEMENT TESTS ====================

class TestClientManagement:
    """Tests for client CRUD operations"""

    def test_add_client_success(self, client, reset_clients, sample_client_data):
        """Test successfully adding a new client"""
        response = client.post('/add-client',
                              data=json.dumps(sample_client_data),
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['client']['name'] == 'Test User'

    def test_add_client_calculates_calories(self, client, reset_clients, sample_client_data):
        """Test that adding a client calculates correct calories"""
        response = client.post('/add-client',
                              data=json.dumps(sample_client_data),
                              content_type='application/json')
        data = json.loads(response.data)
        # Weight 70 * Fat Loss factor 22 = 1540
        assert data['client']['estimated_calories'] == 1540

    def test_add_client_missing_name(self, client, reset_clients):
        """Test that missing name returns error"""
        response = client.post('/add-client',
                              data=json.dumps({'age': 25, 'weight': 70, 'program': 'Fat Loss (FL)'}),
                              content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False

    def test_add_client_missing_program(self, client, reset_clients):
        """Test that missing program returns error"""
        response = client.post('/add-client',
                              data=json.dumps({'name': 'Test', 'age': 25, 'weight': 70}),
                              content_type='application/json')
        assert response.status_code == 400

    def test_add_client_invalid_program(self, client, reset_clients):
        """Test that invalid program returns error"""
        response = client.post('/add-client',
                              data=json.dumps({
                                  'name': 'Test',
                                  'age': 25,
                                  'weight': 70,
                                  'program': 'Invalid Program'
                              }),
                              content_type='application/json')
        assert response.status_code == 400

    def test_get_all_clients(self, client, reset_clients, sample_client_data):
        """Test getting all clients"""
        # Add a client first
        client.post('/add-client',
                   data=json.dumps(sample_client_data),
                   content_type='application/json')

        response = client.get('/clients')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['count'] == 1

    def test_get_specific_client(self, client, reset_clients, sample_client_data):
        """Test getting a specific client by ID"""
        # Add a client first
        add_response = client.post('/add-client',
                                   data=json.dumps(sample_client_data),
                                   content_type='application/json')
        client_id = json.loads(add_response.data)['client']['id']

        response = client.get(f'/client/{client_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['client']['name'] == 'Test User'

    def test_get_nonexistent_client(self, client, reset_clients):
        """Test getting a client that doesn't exist"""
        response = client.get('/client/999')
        assert response.status_code == 404

    def test_delete_client(self, client, reset_clients, sample_client_data):
        """Test deleting a client"""
        # Add a client first
        add_response = client.post('/add-client',
                                   data=json.dumps(sample_client_data),
                                   content_type='application/json')
        client_id = json.loads(add_response.data)['client']['id']

        # Delete the client
        response = client.delete(f'/delete-client/{client_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True

    def test_delete_nonexistent_client(self, client, reset_clients):
        """Test deleting a client that doesn't exist"""
        response = client.delete('/delete-client/999')
        assert response.status_code == 404

    def test_reset_clients(self, client, reset_clients, sample_client_data):
        """Test resetting all clients"""
        # Add a client
        client.post('/add-client',
                   data=json.dumps(sample_client_data),
                   content_type='application/json')

        # Reset all clients
        response = client.post('/reset-clients')
        assert response.status_code == 200

        # Verify clients are empty
        get_response = client.get('/clients')
        data = json.loads(get_response.data)
        assert data['count'] == 0


# ==================== EXPORT TESTS ====================

class TestExportFunctionality:
    """Tests for CSV export functionality"""

    def test_export_csv_no_clients(self, client, reset_clients):
        """Test that export with no clients returns error"""
        response = client.get('/export-csv')
        assert response.status_code == 400

    def test_export_csv_with_clients(self, client, reset_clients, sample_client_data):
        """Test successful CSV export with clients"""
        # Add a client first
        client.post('/add-client',
                   data=json.dumps(sample_client_data),
                   content_type='application/json')

        response = client.get('/export-csv')
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        assert 'Test User' in response.data.decode()


# ==================== BUSINESS LOGIC UNIT TESTS ====================

class TestBusinessLogic:
    """Unit tests for core business logic (calorie factors)"""

    def test_fat_loss_calorie_factor(self):
        """Test Fat Loss calorie factor is correct"""
        assert PROGRAMS['Fat Loss (FL)']['calorie_factor'] == 22

    def test_muscle_gain_calorie_factor(self):
        """Test Muscle Gain calorie factor is correct"""
        assert PROGRAMS['Muscle Gain (MG)']['calorie_factor'] == 35

    def test_beginner_calorie_factor(self):
        """Test Beginner calorie factor is correct"""
        assert PROGRAMS['Beginner (BG)']['calorie_factor'] == 26

    def test_all_programs_have_required_fields(self):
        """Test that all programs have required fields"""
        required_fields = ['workout', 'diet', 'color', 'calorie_factor']
        for program_name, program_data in PROGRAMS.items():
            for field in required_fields:
                assert field in program_data, f"Missing {field} in {program_name}"

    def test_calorie_calculation_formula(self):
        """Test the calorie calculation formula directly"""
        weight = 75
        for program_name, program_data in PROGRAMS.items():
            expected = int(weight * program_data['calorie_factor'])
            assert expected > 0, f"Calorie calculation failed for {program_name}"


# ==================== EDGE CASE TESTS ====================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_add_client_with_zero_weight(self, client, reset_clients):
        """Test adding client with zero weight"""
        response = client.post('/add-client',
                              data=json.dumps({
                                  'name': 'Zero Weight',
                                  'age': 25,
                                  'weight': 0,
                                  'program': 'Fat Loss (FL)'
                              }),
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['client']['estimated_calories'] == 0

    def test_add_client_with_decimal_weight(self, client, reset_clients):
        """Test adding client with decimal weight"""
        response = client.post('/add-client',
                              data=json.dumps({
                                  'name': 'Decimal Weight',
                                  'age': 25,
                                  'weight': 72.5,
                                  'program': 'Fat Loss (FL)'
                              }),
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        # 72.5 * 22 = 1595
        assert data['client']['estimated_calories'] == 1595

    def test_add_multiple_clients(self, client, reset_clients, sample_client_data):
        """Test adding multiple clients"""
        # Add first client
        client.post('/add-client',
                   data=json.dumps(sample_client_data),
                   content_type='application/json')

        # Add second client
        sample_client_data['name'] = 'Second User'
        client.post('/add-client',
                   data=json.dumps(sample_client_data),
                   content_type='application/json')

        response = client.get('/clients')
        data = json.loads(response.data)
        assert data['count'] == 2

    def test_empty_notes_allowed(self, client, reset_clients):
        """Test that empty notes are allowed"""
        response = client.post('/add-client',
                              data=json.dumps({
                                  'name': 'No Notes',
                                  'age': 25,
                                  'weight': 70,
                                  'program': 'Fat Loss (FL)',
                                  'notes': ''
                              }),
                              content_type='application/json')
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

