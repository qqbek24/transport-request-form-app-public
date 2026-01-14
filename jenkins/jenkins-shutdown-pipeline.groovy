pipeline {
    agent { label 'WSL-VM16' }

    parameters {
        string(name: 'BRANCH', defaultValue: 'dev', description: 'Specify the branch name')
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    withCredentials([gitUsernamePassword(credentialsId: 'c5526276-84a5-4328-9968-b0ff64ea094f', gitToolName: 'git-tool')]) {
                        sh 'git clone https://github.com/your-org/transport-request-form-app.git'
                        dir('transport-request-form-app') {
                            sh "git checkout ${params.BRANCH}"
                        }
                    }
                }
            }
        }

        stage('Shutdown Application') {
            steps {
                script {
                    dir('transport-request-form-app') {
                        echo '🛑 Shutting down Transport Request application...'
                        sh 'docker-compose -f docker-compose.yaml down'
                        
                        // Remove orphaned containers
                        sh 'docker-compose -f docker-compose.yaml down --remove-orphans'
                        
                        // Show stopped containers
                        sh 'docker ps -a | grep transport || echo "No transport containers found"'
                        
                        echo '✅ Application stopped successfully'
                        echo '🔍 To verify: Check https://your-production-server.yourdomain.com/ should show 502/503 error'
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ Application shutdown completed!'
            echo '🔍 The application is now stopped on port 5443'
            echo '⚠️  External nginx may show 502/503 errors until properly configured'
        }
        
        failure {
            echo '💥 Shutdown failed! Check logs above.'
        }
    }
}