pipeline {
    agent any

    parameters {
        string(
            name: 'IMAGE_VERSION',
            defaultValue: '',
            description: 'Docker image version tag (e.g. 2.0.1). Leave blank to use the build number.'
        )
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        APP_NAME    = 'aceest-fitness-app'
        DOCKER_IMAGE = 'aceest-fitness-app'
        DOCKER_REGISTRY = 'docker.io'
        APP_VERSION = "${params.IMAGE_VERSION ?: env.BUILD_NUMBER}"
        DOCKER_TAG  = "${APP_NAME}-v${APP_VERSION}"
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Pulling latest code from Git...'
                checkout scm
            }
        }

        stage('Prepare') {
            steps {
                sh 'mkdir -p artifacts reports'
                sh '''
                    cat > artifacts/build-info.txt <<EOF
Build Number: ${BUILD_NUMBER}
App Version: ${APP_VERSION}
Docker Tag:  ${DOCKER_TAG}
Git Commit:  ${GIT_COMMIT}
Git Branch:  ${GIT_BRANCH}
Build Time:  $(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF
                    cat artifacts/build-info.txt
                '''
            }
        }

        stage('Setup Python Environment') {
            steps {
                echo 'Setting up Python environment...'
                sh '''
                    python3 -m venv venv
                    venv/bin/pip install --upgrade pip setuptools wheel
                    venv/bin/pip install -r requirements.txt
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
                    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                    echo "Built: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                '''
            }
        }

        stage('Test Docker Container') {
            steps {
                echo 'Running container smoke test...'
                sh '''
                    docker run -d --name ${APP_NAME}-test-${BUILD_NUMBER} ${DOCKER_IMAGE}:${DOCKER_TAG}

                    sleep 5

                    docker exec ${APP_NAME}-test-${BUILD_NUMBER} \
                        python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/health', timeout=5); print('Health check passed')"
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

                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKERHUB_REPO}:${DOCKER_TAG}
                        docker push ${DOCKERHUB_REPO}:${DOCKER_TAG}

                        echo "Pushed: ${DOCKERHUB_REPO}:${DOCKER_TAG}"

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

