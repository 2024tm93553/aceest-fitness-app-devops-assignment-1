pipeline {
    agent any

    triggers {
        // Poll Git for changes so builds auto-trigger even without webhook setup.
        pollSCM('H/2 * * * *')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        APP_NAME = 'aceest-fitness-app'
        DOCKER_IMAGE = 'aceest-fitness-app'
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_TAG = "${BUILD_NUMBER}"
        APP_VERSION = 'unknown'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Pulling latest code from Git...'
                checkout scm
            }
        }

        stage('Resolve Version Metadata') {
            steps {
                script {
                    env.APP_VERSION = sh(
                        script: "grep -E \"'version':\" app.py | head -1 | sed -E \"s/.*'version': '([^']+)'.*/\\1/\"",
                        returnStdout: true
                    ).trim()

                    if (!env.APP_VERSION) {
                        env.APP_VERSION = "0.0.0"
                    }
                }

                sh '''
                    mkdir -p artifacts reports
                    cat > artifacts/build-info.txt <<EOF
                    Build Number: ${BUILD_NUMBER}
                    Build URL: ${BUILD_URL}
                    Git Commit: ${GIT_COMMIT}
                    Git Branch: ${GIT_BRANCH}
                    App Version: ${APP_VERSION}
                    Build Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
                    EOF
                '''
            }
        }

        stage('Setup Python Environment') {
            steps {
                echo 'Setting up Python environment...'
                sh '''
                    set -e

                    # Install dependencies if missing
                    if [ "$(id -u)" -eq 0 ]; then
                        apt-get update && apt-get install -y python3-venv python3-pip
                    else
                        sudo apt-get update && sudo apt-get install -y python3-venv python3-pip
                    fi

                    python3 --version
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Lint & Syntax Check') {
            steps {
                echo 'Running syntax checks...'
                sh '''
                    venv/bin/python -m py_compile app.py gui_app.py
                    echo "Syntax check passed"
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                echo 'Running unit tests with pytest...'
                sh '''
                    export PYTHONPATH=$PYTHONPATH:.
                    venv/bin/pytest tests/ -v --tb=short --junitxml=reports/pytest-results.xml --cov=. --cov-report=xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/pytest-results.xml'
                    echo 'Test stage completed'
                }
                success {
                    echo 'All tests passed'
                }
                failure {
                    echo 'Some tests failed'
                }
            }
        }

        stage('Create Versioned Build Artifact') {
            steps {
                echo 'Creating versioned source artifact...'
                sh '''
                    ARTIFACT_NAME="${APP_NAME}-v${APP_VERSION}-b${BUILD_NUMBER}.tar.gz"
                    tar -czf "artifacts/${ARTIFACT_NAME}" \
                        app.py gui_app.py requirements.txt Dockerfile pytest.ini \
                        templates static tests
                    echo "${ARTIFACT_NAME}" > artifacts/latest-artifact.txt
                '''
                archiveArtifacts artifacts: 'artifacts/*', fingerprint: true
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'
                sh '''
                    command -v docker >/dev/null 2>&1

                    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:v${APP_VERSION}
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                '''
            }
        }

        stage('Test Docker Container') {
            steps {
                echo 'Running container smoke test...'
                sh '''
                    docker run -d --name ${APP_NAME}-test-${BUILD_NUMBER} -p 9001:9000 ${DOCKER_IMAGE}:${DOCKER_TAG}

                    sleep 5

                    curl -f http://localhost:9001/health || exit 1

                    echo "Container health check passed"
                '''
            }
            post {
                always {
                    sh '''
                        docker stop ${APP_NAME}-test-${BUILD_NUMBER} || true
                        docker rm ${APP_NAME}-test-${BUILD_NUMBER} || true
                    '''
                }
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                echo 'Publishing versioned Docker image tags to Docker Hub...'
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKERHUB_USERNAME', passwordVariable: 'DOCKERHUB_TOKEN')]) {
                    sh '''
                        DOCKERHUB_REPO="${DOCKER_REGISTRY}/${DOCKERHUB_USERNAME}/${APP_NAME}"

                        echo "${DOCKERHUB_TOKEN}" | docker login ${DOCKER_REGISTRY} -u "${DOCKERHUB_USERNAME}" --password-stdin

                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKERHUB_REPO}:build-${BUILD_NUMBER}
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKERHUB_REPO}:v${APP_VERSION}
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKERHUB_REPO}:latest

                        docker push ${DOCKERHUB_REPO}:build-${BUILD_NUMBER}
                        docker push ${DOCKERHUB_REPO}:v${APP_VERSION}
                        docker push ${DOCKERHUB_REPO}:latest

                        docker logout ${DOCKER_REGISTRY}
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                echo 'Quality gate checks...'
                sh '''
                    echo "Checking required project files..."

                    test -f app.py && echo "✅ app.py exists"
                    test -f requirements.txt && echo "✅ requirements.txt exists"
                    test -f Dockerfile && echo "✅ Dockerfile exists"
                    test -d tests && echo "✅ tests directory exists"

                    echo "Quality gate passed"
                '''
            }
        }

        stage('Cleanup') {
            steps {
                echo 'Cleaning up dangling Docker images...'
                sh '''
                    docker image prune -f || true
                '''
            }
        }
    }

    post {
        success {
            echo "BUILD SUCCESSFUL: ${APP_NAME} v${APP_VERSION} (build ${BUILD_NUMBER})"
        }
        failure {
            echo 'BUILD FAILED. Check stage logs for details.'
        }
        always {
            echo "Build #${BUILD_NUMBER} completed"
        }
    }
}

