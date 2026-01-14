pipeline {
    agent { label 'WSL-VM16' }

    parameters {
        string(name: 'BRANCH', defaultValue: 'dev', description: 'Specify the branch name')
        booleanParam(name: 'FORCE_REBUILD', defaultValue: false, description: 'Force rebuild without cache')
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    withCredentials([gitUsernamePassword(credentialsId: 'c5526276-84a5-4328-9968-b0ff64ea094f', gitToolName: 'git-tool')]) {
                        sh 'git clone https://github.com/your-org/transport-request-form-app.git'
                        dir('transport-request-form-app') {
                            sh "git checkout ${params.BRANCH}"
                            // Show current commit for debugging
                            sh 'git log --oneline -3'
                        }
                    }
                }
            }
        }
        
        stage('Clean Docker Cache') {
            when {
                expression { params.FORCE_REBUILD == true }
            }
            steps {
                dir('transport-request-form-app') {
                    // Clean up old containers and images
                    sh 'docker compose -f docker-compose.yaml down --rmi all --volumes || true'
                    sh 'docker system prune -f || true'
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                dir('transport-request-form-app') {
                    script {
                        if (params.FORCE_REBUILD) {
                            // Force rebuild everything without cache
                            sh 'docker compose -f docker-compose.yaml build --no-cache'
                        } else {
                            // Standard build but still force frontend rebuild for env vars
                            sh 'docker compose -f docker-compose.yaml build --no-cache frontend'
                            sh 'docker compose -f docker-compose.yaml build backend'
                        }
                    }
                }
            }
        }
        
        stage('Stop Running Container') {
            steps {
                dir('transport-request-form-app') {
                    sh 'docker compose -f docker-compose.yaml down'
                }
            }
        }
        
        stage('Run Docker Container') {
            steps {
                dir('transport-request-form-app') {
                    sh 'docker compose -f docker-compose.yaml up -d'
                    
                    // Verify deployment
                    sh 'sleep 5'  // Wait for containers to start
                    sh 'docker compose -f docker-compose.yaml ps'
                    
                    // Show frontend environment variables for debugging
                    sh 'docker exec transport-request-form-app-frontend-1 env | grep REACT_APP || true'
                }
            }
        }
        
        stage('Health Check') {
            steps {
                dir('transport-request-form-app') {
                    script {
                        // Check if backend is responding
                        sh '''
                            echo "Testing backend health..."
                            curl -f https://your-production-server.yourdomain.com:5443/api/health || echo "Backend health check failed"
                            
                            echo "Testing frontend accessibility..."
                            curl -f https://your-production-server.yourdomain.com:8000 || echo "Frontend check failed"
                        '''
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean workspace
            deleteDir()
        }
        
        success {
            echo 'Deployment successful! 🚀'
            echo 'Frontend: https://your-production-server.yourdomain.com:8000'
            echo 'Backend API: https://your-production-server.yourdomain.com:5443/docs'
        }
        
        failure {
            echo 'Deployment failed! Check logs above.'
        }
    }
}