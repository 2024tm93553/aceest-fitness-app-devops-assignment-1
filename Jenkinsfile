pipeline {
    agent any

    // Single Parameterized Pipeline – pick any branch at build time.
    // Version is read automatically from the VERSION file in the chosen branch.

    parameters {
        choice(
            name: 'BUILD_BRANCH',
            choices: [
                'develop',
                'main',
                'feature/aceestver-1.0',
                'feature/aceestver-1.1',
                'feature/aceestver-1.1.2',
                'feature/aceestver-2.1.2',
                'feature/aceestver-2.2.1',
                'feature/aceestver-2.2.4',
                'feature/aceestver-3.0.1',
                'feature/aceestver-3.1.2',
                'feature/aceestver-3.2.4'
            ],
            description: 'Select the branch to build and deploy'
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
        APP_NAME        = 'aceest-fitness-app'
        DOCKER_IMAGE    = 'aceest-fitness-app'
        DOCKER_REGISTRY = 'docker.io'
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out branch: ${params.BUILD_BRANCH}"
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "refs/heads/${params.BUILD_BRANCH}"]],
                    userRemoteConfigs: [[
                        url: 'https://github.com/2024tm93553/aceest-fitness-app-devops-assignment-1.git',
                        credentialsId: 'github-credentials'
                    ]]
                ])
            }
        }

        stage('Read Version') {
            steps {
                script {
                    // Read semantic version from the VERSION file in the checked-out branch
                    env.APP_VERSION = readFile('VERSION').trim()
                    env.BUILD_BRANCH = params.BUILD_BRANCH

                    // Determine Docker tag suffix from the selected branch:
                    //   main            → v3.2.4          (no suffix, also tags :latest)
                    //   develop         → v3.2.4-dev
                    //   feature/*       → v3.2.4-feature
                    if (params.BUILD_BRANCH == 'main') {
                        env.DOCKER_SUFFIX = ''
                    } else if (params.BUILD_BRANCH == 'develop') {
                        env.DOCKER_SUFFIX = '-dev'
                    } else {
                        env.DOCKER_SUFFIX = '-feature'
                    }

                    env.VERSIONED_TAG = "v${env.APP_VERSION}${env.DOCKER_SUFFIX}"

                    echo "Branch       : ${params.BUILD_BRANCH}"
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

        stage('SonarQube Analysis') {
            environment {
                SONARQUBE_SERVER = 'SonarQube' // Jenkins SonarQube server name
            }
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        sonar-scanner \
                          -Dsonar.projectKey=aceest-fitness-app \
                          -Dsonar.sources=. \
                          -Dsonar.python.coverage.reportPaths=reports/coverage.xml \
                          -Dsonar.host.url=$SONAR_HOST_URL \
                          -Dsonar.login=$SONAR_AUTH_TOKEN
                    '''
                }
            }
        }

        stage('SonarQube Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
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
                    expression { params.BUILD_BRANCH == 'main' }
                    expression { params.BUILD_BRANCH == 'develop' }
                    expression { params.BUILD_BRANCH.startsWith('feature/aceestver-') }
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
                        if [ "${BUILD_BRANCH}" = "main" ]; then
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
            // Only create a git release tag when building main
            when {
                expression { params.BUILD_BRANCH == 'main' }
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
            echo "BUILD SUCCESSFUL: ${APP_NAME} ${VERSIONED_TAG} (build ${BUILD_NUMBER}) [branch: ${BUILD_BRANCH}]"
        }
        failure {
            echo "BUILD FAILED: ${APP_NAME} on branch ${BUILD_BRANCH}. Check stage logs for details."
        }
        always {
            echo "Build #${BUILD_NUMBER} completed for branch ${BUILD_BRANCH}"
        }
    }
}

