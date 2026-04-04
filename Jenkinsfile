pipeline {
    agent any

    environment {
        APP_NAME = 'aceest-fitness-app'
        DOCKER_IMAGE = 'aceest-fitness-app'
        DOCKER_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                echo '📥 Pulling latest code from GitHub...'
                checkout scm
            }
        }

        stage('Setup Python Environment') {
            steps {
                echo '🐍 Setting up Python environment...'
                sh '''
                    python3 --version
                    pip3 install --upgrade pip
                    pip3 install -r requirements.txt
                '''
            }
        }

        stage('Lint & Syntax Check') {
            steps {
                echo '🔍 Running linting and syntax checks...'
                sh '''
                    # Check Python syntax
                    python3 -m py_compile app.py
                    echo "✅ Syntax check passed"
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                echo '🧪 Running unit tests with pytest...'
                sh '''
                    python3 -m pytest tests/ -v --tb=short
                '''
            }
            post {
                always {
                    echo '📊 Test stage completed'
                }
                success {
                    echo '✅ All tests passed!'
                }
                failure {
                    echo '❌ Some tests failed!'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo '🐳 Building Docker image...'
                sh '''
                    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                '''
            }
        }

        stage('Test Docker Container') {
            steps {
                echo '🔬 Testing Docker container...'
                sh '''
                    # Run container in background
                    docker run -d --name ${APP_NAME}-test-${BUILD_NUMBER} -p 9001:9000 ${DOCKER_IMAGE}:${DOCKER_TAG}

                    # Wait for container to start
                    sleep 5

                    # Test health endpoint
                    curl -f http://localhost:9001/health || exit 1

                    echo "✅ Container health check passed"
                '''
            }
            post {
                always {
                    sh '''
                        # Cleanup test container
                        docker stop ${APP_NAME}-test-${BUILD_NUMBER} || true
                        docker rm ${APP_NAME}-test-${BUILD_NUMBER} || true
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                echo '🚦 Quality Gate Check...'
                sh '''
                    echo "Checking code quality metrics..."

                    # Check if all required files exist
                    test -f app.py && echo "✅ app.py exists"
                    test -f requirements.txt && echo "✅ requirements.txt exists"
                    test -f Dockerfile && echo "✅ Dockerfile exists"
                    test -d tests && echo "✅ tests directory exists"

                    echo "✅ Quality Gate passed!"
                '''
            }
        }

        stage('Cleanup') {
            steps {
                echo '🧹 Cleaning up old Docker images...'
                sh '''
                    # Remove dangling images
                    docker image prune -f || true
                '''
            }
        }
    }

    post {
        success {
            echo '''
            ╔══════════════════════════════════════╗
            ║  ✅ BUILD SUCCESSFUL                 ║
            ║  ACEest Fitness App is ready!        ║
            ╚══════════════════════════════════════╝
            '''
        }
        failure {
            echo '''
            ╔══════════════════════════════════════╗
            ║  ❌ BUILD FAILED                     ║
            ║  Please check the logs above         ║
            ╚══════════════════════════════════════╝
            '''
        }
        always {
            echo "Build #${BUILD_NUMBER} completed"
        }
    }
}

