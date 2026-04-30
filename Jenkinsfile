pipeline {
    agent any

    // No manual IMAGE_VERSION parameter – version is read from the VERSION file in each branch.
    // Jenkins Multibranch Pipeline auto-discovers all feature/*, develop, and main branches.

    triggers {
        pollSCM('H/2 * * * *')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        APP_NAME        = 'aceest-fitness-app'
        DOCKER_IMAGE    = 'aceest-fitness-app'
        DOCKER_REGISTRY = 'docker.io'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Pulling latest code from Git...'
                checkout scm
            }
        }

        stage('Read Version') {
            steps {
                script {
                    // Read semantic version from the VERSION file committed in each branch
                    env.APP_VERSION = readFile('VERSION').trim()

                    // Determine Docker tag suffix by branch type:
                    //   main            → v3.2.4          (no suffix, also tags :latest)
                    //   develop         → v3.2.4-dev
                    //   feature/aceest* → v3.2.4-feature
                    if (env.BRANCH_NAME == 'main') {
                        env.DOCKER_SUFFIX = ''
                    } else if (env.BRANCH_NAME == 'develop') {
                        env.DOCKER_SUFFIX = '-dev'
                    } else {
                        env.DOCKER_SUFFIX = '-feature'
                    }

                    env.VERSIONED_TAG = "v${env.APP_VERSION}${env.DOCKER_SUFFIX}"

                    echo "Branch       : ${env.BRANCH_NAME}"
                    echo "App version  : ${env.APP_VERSION}"
                    echo "Versioned tag: ${env.VERSIONED_TAG}"
                }
            }
        }

        stage('Prepare') {
            steps {
                sh 'mkdir -p artifacts reports'
                sh '''
                    cat > artifacts/build-info.txt <<EOF
Build Number: ${BUILD_NUMBER}
App Version: ${APP_VERSION}
Versioned Tag: ${VERSIONED_TAG}
Git Branch:  ${BRANCH_NAME}
Git Commit:  ${GIT_COMMIT}
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
                    venv/bin/python -m py_compile app.py
                    echo "Syntax check passed"
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                echo 'Running unit tests with pytest...'
                sh '''
                    export PYTHONPATH=$PYTHONPATH:.
                    export MPLBACKEND=Agg
                    venv/bin/pytest tests/ -v --tb=short --junitxml=reports/pytest-results.xml --cov=app --cov-report=xml
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
                    ARTIFACT_NAME="${APP_NAME}-${VERSIONED_TAG}-b${BUILD_NUMBER}.tar.gz"
                    tar -czf "artifacts/${ARTIFACT_NAME}" \
                        app.py VERSION requirements.txt Dockerfile pytest.ini \
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
                    docker build -t ${DOCKER_IMAGE}:${VERSIONED_TAG} .
                    echo "Built: ${DOCKER_IMAGE}:${VERSIONED_TAG}"
                '''
            }
        }

        stage('Test Docker Container') {
            steps {
                echo 'Running container smoke test...'
                sh '''
                    docker run -d --name ${APP_NAME}-test-${BUILD_NUMBER} ${DOCKER_IMAGE}:${VERSIONED_TAG}

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
            // Push on all tracked branches: feature/aceestver-*, develop, main
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    branch pattern: 'feature/aceestver-*', comparator: 'GLOB'
                }
            }
            steps {
                echo "Publishing Docker image for branch: ${env.BRANCH_NAME}"
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials',
                                                  usernameVariable: 'DOCKERHUB_USERNAME',
                                                  passwordVariable: 'DOCKERHUB_TOKEN')]) {
                    sh '''
                        DOCKERHUB_REPO="${DOCKER_REGISTRY}/${DOCKERHUB_USERNAME}/${APP_NAME}"

                        echo "${DOCKERHUB_TOKEN}" | docker login ${DOCKER_REGISTRY} -u "${DOCKERHUB_USERNAME}" --password-stdin

                        # Push the versioned tag (e.g. v1.0-feature / v2.2.1-dev / v3.2.4)
                        docker tag ${DOCKER_IMAGE}:${VERSIONED_TAG} ${DOCKERHUB_REPO}:${VERSIONED_TAG}
                        docker push ${DOCKERHUB_REPO}:${VERSIONED_TAG}
                        echo "Pushed: ${DOCKERHUB_REPO}:${VERSIONED_TAG}"

                        # On main: also push :latest
                        if [ "${BRANCH_NAME}" = "main" ]; then
                            docker tag ${DOCKER_IMAGE}:${VERSIONED_TAG} ${DOCKERHUB_REPO}:latest
                            docker push ${DOCKERHUB_REPO}:latest
                            echo "Pushed: ${DOCKERHUB_REPO}:latest"
                        fi

                        docker logout ${DOCKER_REGISTRY}
                    '''
                }
            }
        }

        stage('Tag Git Release') {
            // Only create a git release tag when merging into main
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-credentials',
                                                  usernameVariable: 'GH_USER',
                                                  passwordVariable: 'GH_TOKEN')]) {
                    sh '''
                        git config user.email "jenkins@aceest.ci"
                        git config user.name "Jenkins CI"

                        TAG_NAME="v${APP_VERSION}"

                        # Only create tag if it does not already exist
                        if ! git rev-parse "${TAG_NAME}" >/dev/null 2>&1; then
                            git tag -a "${TAG_NAME}" -m "Release ${TAG_NAME} – build ${BUILD_NUMBER}"
                            git push https://${GH_USER}:${GH_TOKEN}@$(git remote get-url origin | sed 's|https://||') "${TAG_NAME}"
                            echo "Tagged and pushed: ${TAG_NAME}"
                        else
                            echo "Tag ${TAG_NAME} already exists, skipping."
                        fi
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                echo 'Quality gate checks...'
                sh '''
                    echo "Checking required project files..."

                    test -f app.py       && echo "app.py exists"
                    test -f VERSION      && echo "VERSION file exists: $(cat VERSION)"
                    test -f requirements.txt && echo "requirements.txt exists"
                    test -f Dockerfile   && echo "Dockerfile exists"
                    test -d tests        && echo "tests/ directory exists"

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
            echo "BUILD SUCCESSFUL: ${APP_NAME} ${VERSIONED_TAG} (build ${BUILD_NUMBER}) [branch: ${BRANCH_NAME}]"
        }
        failure {
            echo "BUILD FAILED: ${APP_NAME} on branch ${BRANCH_NAME}. Check stage logs for details."
        }
        always {
            echo "Build #${BUILD_NUMBER} completed for branch ${BRANCH_NAME}"
        }
    }
}

