pipeline {
    agent {
        docker {
            image 'python:3.10-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }
    
    environment {
        ALLURE_TESTOPS_ENDPOINT = credentials('allure-testops-endpoint')
        ALLURE_TESTOPS_TOKEN = credentials('allure-testops-token')
        ALLURE_TESTOPS_PROJECT_ID = credentials('allure-testops-project-id')
        ALLURE_RESULTS = 'allure-results'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup') {
            steps {
                sh '''
                    python -m pip install --upgrade pip
                    pip install -e .
                    pip install pytest allure-pytest allurectl
                '''
            }
        }
        
        stage('Download Allurectl') {
            steps {
                sh '''
                    curl -o allurectl https://github.com/allure-framework/allurectl/releases/latest/download/allurectl_linux_amd64
                    chmod +x allurectl
                    ./allurectl --version
                '''
            }
        }
        
        stage('Run Tests') {
            steps {
                sh '''
                    mkdir -p ${ALLURE_RESULTS}
                    python -m pytest tests \
                        --alluredir=${ALLURE_RESULTS} \
                        --allure-features="SQL Generator,API,Database Integration" \
                        --allure-epics="SQL Generation,API Integration,Database" \
                        --allure-link-pattern=issue:https://github.com/beCharlatan/sql_extractor/issues/{} \
                        --allure-link-pattern=tms:https://testops.example.com/testcase/{}
                '''
            }
        }
        
        stage('Upload to Allure TestOps') {
            steps {
                sh '''
                    ./allurectl upload \
                        --endpoint ${ALLURE_TESTOPS_ENDPOINT} \
                        --token ${ALLURE_TESTOPS_TOKEN} \
                        --project-id ${ALLURE_TESTOPS_PROJECT_ID} \
                        --launch-name "SQL Extractor Tests" \
                        --launch-tags "CI,Jenkins" \
                        ${ALLURE_RESULTS}
                '''
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'allure-results/**', allowEmptyArchive: true
            
            // Генерация HTML-отчета Allure
            sh '''
                pip install allure-commandline
                allure generate ${ALLURE_RESULTS} -o allure-report --clean
            '''
            
            // Публикация HTML-отчета
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'allure-report',
                reportFiles: 'index.html',
                reportName: 'Allure Report',
                reportTitles: 'Allure Report'
            ])
            
            // Очистка
            cleanWs()
        }
    }
}
