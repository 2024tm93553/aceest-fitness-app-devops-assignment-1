# ACEest Fitness & Gym Management System

**DevOps Assignment - Version 1.1.2**

A comprehensive fitness and gym management application with both GUI (Tkinter) and REST API (Flask) interfaces.

---

## 🎯 Project Overview

This project demonstrates modern DevOps practices including:
- ✅ Version Control with Git/GitHub
- ✅ Containerization with Docker
- ✅ Automated Testing with Pytest
- ✅ CI/CD Pipeline with GitHub Actions
- ✅ Jenkins Integration for BUILD phase

---

## 📁 Project Structure

```
aceest-fitness-app/
├── app.py                  # Flask REST API (for Docker/CI/CD)
├── gui_app.py             # Tkinter GUI application (original)
├── requirements.txt       # Python dependencies
├── tests/                 # Pytest test suite (Phase 2)
├── Dockerfile            # Container definition (Phase 4)
├── .github/
│   └── workflows/
│       └── main.yml      # GitHub Actions CI/CD (Phase 6)
└── README.md             # This file
```

---

## 🚀 Features

### Fitness Programs
1. **Fat Loss (FL)** - Calorie factor: 22 kcal/kg
2. **Muscle Gain (MG)** - Calorie factor: 35 kcal/kg
3. **Beginner (BG)** - Calorie factor: 26 kcal/kg

### Capabilities
- Client management (add, view, export)
- Personalized workout and nutrition plans
- Calorie estimation based on weight and program
- Progress tracking with charts
- CSV export functionality

---

## 💻 Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/aceest-fitness-app-devops-assignment-1.git
cd aceest-fitness-app-devops-assignment-1

# Install dependencies
pip install -r requirements.txt
```

---

## 🏃 Running the Application

### Option 1: Flask REST API (Recommended for DevOps Pipeline)

```bash
python app.py
```

The API will be available at: `http://localhost:5000`

**Test the API:**
```bash
# Service info
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health

# Get all programs
curl http://localhost:5000/api/programs

# Calculate calories
curl -X POST http://localhost:5000/api/calculate-calories \
  -H "Content-Type: application/json" \
  -d '{"weight": 70, "program": "Fat Loss (FL)"}'
```

### Option 2: GUI Application

```bash
python gui_app.py
```

This launches the Tkinter desktop application with full GUI interface.

---

## 🧪 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service information |
| GET | `/health` | Health check |
| GET | `/api/programs` | List all programs |
| GET | `/api/programs/<name>` | Get program details |
| POST | `/api/calculate-calories` | Calculate calories |
| GET | `/api/calculate-calories/<name>?weight=X` | Calculate calories (GET) |

---

## 📊 Example API Usage

### Get Program Details
```bash
curl http://localhost:5000/api/programs/Fat%20Loss%20%28FL%29
```

### Calculate Calories
```bash
curl -X POST http://localhost:5000/api/calculate-calories \
  -H "Content-Type: application/json" \
  -d '{
    "weight": 75,
    "program": "Muscle Gain (MG)"
  }'
```

**Response:**
```json
{
  "success": true,
  "weight_kg": 75.0,
  "program": "Muscle Gain (MG)",
  "estimated_daily_calories": 2625,
  "calorie_factor": 35
}
```

---

## 🐳 Docker (Phase 4)

```bash
# Build Docker image
docker build -t aceest-fitness:latest .

# Run container
docker run -p 5000:5000 aceest-fitness:latest

# Access API
curl http://localhost:5000/health
```

---

## 🧪 Testing (Phase 3)

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test
pytest tests/test_app.py::test_health_endpoint -v
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions
Automatically triggered on:
- Push to `main` or `develop` branch
- Pull requests to `main`

**Pipeline stages:**
1. ✅ Code checkout
2. ✅ Python environment setup
3. ✅ Dependency installation
4. ✅ Linting with flake8
5. ✅ Unit tests with pytest
6. ✅ Docker image build
7. ✅ Container smoke test

### Jenkins BUILD
Jenkins pulls code from GitHub and executes:
1. Environment setup
2. Dependency installation
3. Unit tests
4. Docker image build
5. Artifact archival

---

## 📝 Development Workflow

### Branching Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes

### Commit Messages
Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `chore:` - Maintenance

---

## 🛠️ Tech Stack

- **Backend**: Flask 3.0.0
- **GUI**: Tkinter
- **Data Visualization**: Matplotlib 3.8.2
- **Testing**: Pytest 7.4.3
- **Containerization**: Docker
- **CI/CD**: GitHub Actions, Jenkins
- **Version Control**: Git, GitHub

---

## 📈 Project Phases

- [x] **Phase 1**: Application Development ✅
- [ ] **Phase 2**: Unit Testing Framework
- [ ] **Phase 3**: Version Control Strategy
- [ ] **Phase 4**: Docker Containerization
- [ ] **Phase 5**: Jenkins BUILD Configuration
- [ ] **Phase 6**: GitHub Actions CI/CD Pipeline
- [ ] **Phase 7**: Documentation & Deployment

---

## 👨‍💻 Author

**Student ID**: 2024tm93553  
**Course**: DevOps Assignment 1  
**Institution**: BITS Pilani

---

## 📄 License

This project is created for educational purposes as part of a DevOps assignment.

---

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
python app.py --port 5001
```

### Matplotlib Backend Issues (macOS)
```bash
# If GUI app doesn't display charts
pip install --upgrade matplotlib
```

### Permission Denied
```bash
# Make scripts executable
chmod +x app.py gui_app.py
```

---

## 🔗 Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Last Updated**: April 2, 2026  
**Version**: 1.1.2

