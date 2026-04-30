# 🏋️ ACEest Fitness & Gym Management System

![Version](https://img.shields.io/badge/version-2.0.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-red.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-yellow.svg)
![License](https://img.shields.io/badge/license-Educational-lightgrey.svg)

> **DevOps Assignment** - A comprehensive fitness management application demonstrating modern DevOps practices including containerization, CI/CD pipelines, and automated testing.

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Docker](#-docker)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Jenkins Integration](#-jenkins-integration)
- [Development Workflow](#-development-workflow)
- [Troubleshooting](#-troubleshooting)
- [Author](#-author)

---

## 🎯 Project Overview

This project demonstrates modern DevOps practices through a fitness and gym management application:

| Phase | Component | Status |
|-------|-----------|--------|
| Phase 1 | Application Development & Modularization | ✅ Complete |
| Phase 2 | Version Control System (VCS) Strategy | ✅ Complete |
| Phase 3 | Unit Testing & Validation Framework | ✅ Complete |
| Phase 4 | Containerization with Docker | ✅ Complete |
| Phase 5 | Jenkins BUILD & Quality Gate | ✅ Complete |
| Phase 6 | GitHub Actions CI/CD Pipeline | ✅ Complete |

---

## ✨ Features

### Fitness Programs

| Program | Code | Calorie Factor | Workout Focus |
|---------|------|----------------|---------------|
| Fat Loss | FL | 22 kcal/kg | Cardio, HIIT, Recovery |
| Muscle Gain | MG | 35 kcal/kg | Strength Training |
| Beginner | BG | 26 kcal/kg | Foundation Building |

### Application Capabilities

- 👥 **Client Management** - Add, view, update, and delete clients
- 📊 **Progress Tracking** - Weekly adherence logging with SQLite persistence
- 🍽️ **Nutrition Planning** - Personalized calorie recommendations
- 📈 **Data Visualization** - Progress charts with Matplotlib
- 📤 **CSV Export** - Export client data for external analysis
- 🔗 **REST API** - Full-featured API for integrations

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Flask 3.0.0, Python 3.11+ |
| **Database** | SQLite (persistent storage) |
| **Testing** | Pytest 7.4.3, pytest-flask |
| **Containerization** | Docker (multi-stage build) |
| **CI/CD** | GitHub Actions |
| **Build Server** | Jenkins |
| **Version Control** | Git, GitHub |

---

## 📁 Project Structure

```
aceest-fitness-app-devops-assignment-1/
├── app.py                      # Flask REST API (main application)
├── gui_app.py                  # Tkinter GUI application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Optimized multi-stage Docker build
├── Jenkinsfile                 # Jenkins pipeline configuration
├── pytest.ini                  # Pytest configuration
├── aceest_fitness.db           # SQLite database (auto-generated)
│
├── tests/                      # Test suite
│   ├── __init__.py
│   └── test_app.py            # 50+ comprehensive unit tests
│
├── templates/                  # HTML templates
│   └── dashboard.html
│
├── static/                     # Static assets
│   ├── css/
│   │   └── dashboard.css
│   └── js/
│       └── dashboard.js
│
├── .github/
│   └── workflows/
│       └── main.yml           # GitHub Actions CI/CD workflow
│
└── README.md                   # This documentation
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Docker (for containerization)
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/2024tm93553/aceest-fitness-app-devops-assignment-1.git
cd aceest-fitness-app-devops-assignment-1

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

The API will be available at: **http://localhost:9000**

---

## 🏃 Running the Application

### Option 1: Flask REST API (Recommended)

```bash
python app.py
```

**Quick Test:**
```bash
# Health check
curl http://localhost:9000/health

# Service info
curl http://localhost:9000/

# List all programs
curl http://localhost:9000/api/programs
```

### Option 2: Docker Container

```bash
# Build versioned images for Docker Hub
docker build -t docker.io/<dockerhub-username>/aceest-fitness-app:2.0.1 \
  -t docker.io/<dockerhub-username>/aceest-fitness-app:latest .

# Push both tags to Docker Hub
docker login docker.io
docker push docker.io/<dockerhub-username>/aceest-fitness-app:2.0.1
docker push docker.io/<dockerhub-username>/aceest-fitness-app:latest

# Run the container
docker run -d -p 9000:9000 --name aceest-app \
  docker.io/<dockerhub-username>/aceest-fitness-app:2.0.1

# Verify it's running
curl http://localhost:9000/health
```

### Option 3: Podman Container

```bash
# Build the same Dockerfile with Podman
podman build -f Dockerfile \
  -t docker.io/<dockerhub-username>/aceest-fitness-app:2.0.1 \
  -t docker.io/<dockerhub-username>/aceest-fitness-app:latest .

# Push both tags to Docker Hub
podman login docker.io
podman push docker.io/<dockerhub-username>/aceest-fitness-app:2.0.1
podman push docker.io/<dockerhub-username>/aceest-fitness-app:latest

# Run the container
podman run -d -p 9000:9000 --name aceest-app \
  docker.io/<dockerhub-username>/aceest-fitness-app:2.0.1
```

### Option 4: GUI Application

```bash
python gui_app.py
```

---

## 📖 API Documentation

### Base URL
```
http://localhost:9000
```

### Endpoints

#### Health & Info

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service information and available endpoints |
| `GET` | `/health` | Health check with database status |
| `GET` | `/dashboard` | Web GUI interface |

#### Programs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/programs` | List all fitness programs |
| `GET` | `/api/programs/<name>` | Get specific program details |

#### Calorie Calculation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/calculate-calories` | Calculate daily calories |
| `GET` | `/api/calculate-calories/<program>?weight=X` | Calculate calories (GET) |

#### Client Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/clients` | List all clients |
| `GET` | `/client/<id>` | Get client by ID |
| `GET` | `/client/name/<name>` | Get client by name |
| `POST` | `/add-client` | Add new client |
| `DELETE` | `/delete-client/<id>` | Delete a client |
| `POST` | `/reset-clients` | Reset all client data |

#### Progress Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/save-progress` | Log weekly progress |
| `GET` | `/progress/<client_name>` | Get progress history |
| `GET` | `/progress-chart` | Generate progress chart |

#### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/export-csv` | Export clients to CSV |

### Example Requests

**Add a Client:**
```bash
curl -X POST http://localhost:9000/add-client \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 28,
    "weight": 75,
    "program": "Muscle Gain (MG)",
    "adherence": 85,
    "notes": "Morning workouts preferred"
  }'
```

**Calculate Calories:**
```bash
curl -X POST http://localhost:9000/api/calculate-calories \
  -H "Content-Type: application/json" \
  -d '{"weight": 75, "program": "Muscle Gain (MG)"}'
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

## 🧪 Testing

### Run All Tests

```bash
# Run full test suite (50 tests)
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=html

# Run specific test class
pytest tests/test_app.py::TestClientManagement -v

# Run specific test
pytest tests/test_app.py::TestHealthEndpoint::test_health_returns_200 -v
```

### Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| Health Endpoint | 4 | API health checks |
| Home Endpoint | 3 | Service info validation |
| Programs API | 5 | Program CRUD operations |
| Calorie Calculation | 7 | Business logic validation |
| Client Management | 12 | Client CRUD operations |
| Export Functionality | 2 | CSV export tests |
| Business Logic | 5 | Core formula validation |
| Edge Cases | 4 | Boundary conditions |
| Progress Tracking | 6 | v2.0.1 features |
| Database Persistence | 3 | SQLite integration |

**Total: 50+ tests with comprehensive coverage**

---

## 🐳 Docker

### Dockerfile Optimizations

The Dockerfile is optimized for **size** and **security**:

| Optimization | Benefit |
|--------------|---------|
| Multi-stage build | Reduces final image size by ~60% |
| Python 3.11-slim base | Minimal OS footprint |
| Non-root user | Security best practice |
| No shell access | Prevents shell injection |
| Health check | Container orchestration ready |
| Layer caching | Faster rebuilds |
| Removed build tools | Smaller attack surface |

### Docker Commands

```bash
# Build image locally
docker build -t aceest-fitness:latest .

# Run container
docker run -d -p 9000:9000 --name aceest-app aceest-fitness:latest

# Tag for Docker Hub version control
docker tag aceest-fitness:latest docker.io/<dockerhub-username>/aceest-fitness-app:v2.0.1
docker tag aceest-fitness:latest docker.io/<dockerhub-username>/aceest-fitness-app:latest

# Publish to Docker Hub
docker login docker.io
docker push docker.io/<dockerhub-username>/aceest-fitness-app:v2.0.1
docker push docker.io/<dockerhub-username>/aceest-fitness-app:latest

# View logs
docker logs aceest-app

# Stop container
docker stop aceest-app

# Remove container
docker rm aceest-app

# Run tests against the image using the local test suite
docker run --rm -v "$PWD/tests:/app/tests:ro" aceest-fitness:latest python -m pytest tests/ -v
```

### Podman Commands

```bash
# Build and tag from the same Dockerfile
podman build -f Dockerfile -t aceest-fitness:latest .
podman tag aceest-fitness:latest docker.io/<dockerhub-username>/aceest-fitness-app:v2.0.1
podman tag aceest-fitness:latest docker.io/<dockerhub-username>/aceest-fitness-app:latest

# Publish to Docker Hub
podman login docker.io
podman push docker.io/<dockerhub-username>/aceest-fitness-app:v2.0.1
podman push docker.io/<dockerhub-username>/aceest-fitness-app:latest

# Run with Podman
podman run -d -p 9000:9000 --name aceest-app aceest-fitness:latest
```

### Registry Tagging Strategy

- `build-<jenkins-build-number>` keeps each CI build immutable.
- `v<application-version>` tracks release-oriented image versions.
- `latest` always points at the newest published image.

### Jenkins Docker Hub Publishing

The Jenkins pipeline publishes the tested image to Docker Hub using the repository pattern below:

```text
docker.io/<dockerhub-username>/aceest-fitness-app
```

Configure this Jenkins credential before running the pipeline:

- Credential ID: `dockerhub-credentials`
- Type: `Username with password`
- Username: Docker Hub username
- Password: Docker Hub access token

### Image Size Comparison

| Build Type | Approximate Size |
|------------|------------------|
| Without optimization | ~1.2 GB |
| With multi-stage | ~450 MB |

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The pipeline (`.github/workflows/main.yml`) is triggered on:
- ✅ Push to `main` or `develop` branch
- ✅ Pull requests to `main`

### Pipeline Stages

```
┌─────────────────┐
│   Code Checkout │
└────────┬────────┘
         │
┌────────▼────────┐
│  Setup Python   │
│     3.11        │
└────────┬────────┘
         │
┌────────▼────────┐
│    Install      │
│  Dependencies   │
└────────┬────────┘
         │
┌────────▼────────┐
│   Lint Code     │
│   (flake8)      │
└────────┬────────┘
         │
┌────────▼────────┐
│   Run Tests     │
│   (pytest)      │
└────────┬────────┘
         │
┌────────▼────────┐
│  Build Docker   │
│     Image       │
└────────┬────────┘
         │
┌────────▼────────┐
│  Smoke Test     │
│   Container     │
└─────────────────┘
```

---

## 🔧 Jenkins Integration

### Prerequisites

1. Jenkins server running (port 8080)
2. Required plugins: Pipeline, Git, Docker

### Setup Jenkins Job

1. **Create New Pipeline Job**
   - New Item → Pipeline → Enter name "aceest-fitness-app"

2. **Configure Pipeline**
   - Definition: Pipeline script from SCM
   - SCM: Git
   - Repository URL: `https://github.com/2024tm93553/aceest-fitness-app-devops-assignment-1.git`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`

3. **Build Triggers**
  - Poll SCM: `H/2 * * * *` (every ~2 minutes)
   - Or use GitHub webhook for instant builds

### Jenkinsfile Stages

```groovy
pipeline {
    stages {
    stage('Checkout')                     // Pull latest code
    stage('Resolve Version Metadata')     // Read app version + build info
    stage('Setup Python Environment')     // Install dependencies
    stage('Lint & Syntax Check')          // Python compile checks
    stage('Unit Tests')                   // Run pytest + JUnit report
    stage('Create Versioned Build Artifact')
    stage('Build Docker Image')           // Build + tag image
    stage('Test Docker Container')        // Smoke-test /health
    stage('Quality Gate')                 // Required-file validation
    stage('Cleanup')                      // Remove dangling images
    }
}
```

### Build Artifacts (Step 4 requirement)

- Versioned archive: `aceest-fitness-app-v<app_version>-b<build_number>.tar.gz`
- Build metadata: `artifacts/build-info.txt`
- Test report: `reports/pytest-results.xml`
- All artifacts are archived in Jenkins for each build.

### Running Jenkins Locally

```bash
# Start Jenkins container
docker run -d --name jenkins \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts

# Get initial admin password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

---

## 📝 Development Workflow

### Branch Strategy

```
main (production)
  │
  └── develop (integration)
        │
        ├── feature/sqlite-database-v2.0.1
        ├── feature/progress-tracking
        ├── bugfix/calorie-calculation
        └── hotfix/security-patch
```

### Commit Message Convention

```
<type>(<scope>): <description>

Types:
- feat:     New feature
- fix:      Bug fix
- docs:     Documentation
- test:     Adding tests
- refactor: Code refactoring
- chore:    Maintenance
- ci:       CI/CD changes

Examples:
- feat(api): add progress tracking endpoint
- fix(db): resolve SQLite connection leak
- test(client): add edge case tests
- docs(readme): update API documentation
```

### Pull Request Flow

1. Create feature branch from `develop`
2. Make changes and commit
3. Push branch and create PR to `develop`
4. CI pipeline runs automatically
5. Code review and approval
6. Merge to `develop`
7. When ready, PR from `develop` to `main`

---

## 🆘 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 9000
lsof -i :9000

# Kill the process
kill -9 <PID>

# Or run on different port
FLASK_RUN_PORT=5000 python app.py
```

#### Docker Build Fails
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t aceest-fitness:latest .
```

#### Tests Failing
```bash
# Reset test database
rm -f aceest_fitness.db

# Run tests with verbose output
pytest tests/ -v --tb=long
```

#### Jenkins Cannot Access GitHub
```bash
# Check if SSH key is configured
ssh -T git@github.com

# Or use HTTPS with personal access token
```

#### Matplotlib Display Issues (macOS)
```bash
# Install backend
pip install --upgrade matplotlib
export MPLBACKEND=Agg
```

---

## 👨‍💻 Author

| Field | Value |
|-------|-------|
| **Student ID** | 2024tm93553 |
| **Course** | DevOps Engineering |
| **Assignment** | Assignment 1 |
| **Institution** | BITS Pilani |

---

## 📄 License

This project is created for **educational purposes** as part of a DevOps assignment at BITS Pilani.

---

## 🙏 Acknowledgments

- BITS Pilani - DevOps Course Team
- Flask Documentation
- Docker Best Practices Guide
- GitHub Actions Documentation

---

<div align="center">

**Made with ❤️ for DevOps Learning**

[⬆ Back to Top](#-aceest-fitness--gym-management-system)

</div>

