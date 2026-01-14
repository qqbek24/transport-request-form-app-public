pipeline {
    agent { label 'WSL-VM16' }

    // ========================================
    // CENTRALIZED CONFIGURATION
    // ========================================
    environment {
        // Container names
        BACKEND_CONTAINER = 'transport-request-form-app-backend-1'
        FRONTEND_CONTAINER = 'transport-request-form-app-frontend-1'
        
        // JSON Backup paths (must match config.yaml paths.json_backup_file)
        JSON_BACKUP_PATH = '/tmp/transport_requests.json'
        JSON_BACKUP_DIR = '/tmp/transport-backups'
        JSON_BACKUP_PREFIX = 'transport_'
        JSON_LATEST = 'latest.json'
        
        // Backup settings
        JSON_MIN_SIZE = '10'  // Minimum file size in bytes
        JSON_MAX_COUNT = '10'  // Keep only last N backups
        
        // Logs paths
        LOGS_DIR_CONTAINER = '/tmp/logs'
        LOGS_BACKUP_DIR = '/tmp/transport-logs-backup'
        
        // SSL Certificates
        SSL_CERTS_DIR = '/tmp/jenkins-ssl-certs'
        SSL_CERT_FILE = 'europe.crt'
        SSL_KEY_FILE = 'europe.key'
        
        // Server configuration (for health checks)
        SERVER_HOST = 'your-production-server.yourdomain.com'
        BACKEND_PORT = '8010'
        FRONTEND_PORT = '8002'
        
        // Docker compose
        COMPOSE_FILE = 'docker-compose.yaml'
        REPO_DIR = 'transport-request-form-app'
    }

    parameters {
        string(name: 'BRANCH', defaultValue: 'dev', description: 'Specify the branch name')
        booleanParam(name: 'FORCE_REBUILD', defaultValue: false, description: 'Force rebuild without cache')
        choice(name: 'ACTION', choices: ['deploy', 'shutdown'], description: 'Choose action: deploy or shutdown')
        booleanParam(name: 'USE_CUSTOM_CERTS', defaultValue: false, description: 'Upload NEW SSL certificates (check only when updating new certs)')
        file(name: 'SSL_CERT', description: 'SSL Certificate (.crt file) - upload only when updating certificates')
        file(name: 'SSL_KEY', description: 'SSL Private Key (.key file) - upload only when updating certificates')
        password(name: 'DEBUG_SECRET_KEY', defaultValue: '', description: '🔐 OPTIONAL: Debug mode secret key for maintenance access (leave empty to disable debug features)')
        booleanParam(name: 'USE_TOKEN_MANAGER', defaultValue: true, description: '🔄 Use Token Manager (automatic token refresh) instead of manual token')
        text(name: 'MANUAL_SHAREPOINT_TOKEN', defaultValue: '', description: '⚠️ LEGACY: Manual SHAREPOINT_ACCESS_TOKEN (only if Token Manager disabled)')
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    // DEFENSIVE BACKUP - Backup JSON file from running container before cleanup
                    sh '''
                        # Check if backend container is running
                        if docker ps --format '{{.Names}}' | grep -q "${BACKEND_CONTAINER}"; then
                            echo "💾 Backing up JSON data from running container..."
                            mkdir -p ${JSON_BACKUP_DIR}
                            
                            # Check file size in container before backup (prevent overwriting good backup with empty file)
                            FILE_SIZE=$(docker exec ${BACKEND_CONTAINER} stat -c%s ${JSON_BACKUP_PATH} 2>/dev/null || echo 0)
                            echo "📊 JSON file size in container: $FILE_SIZE bytes"
                            
                            if [ "$FILE_SIZE" -gt ${JSON_MIN_SIZE} ]; then
                                # Valid file - create timestamped backup
                                TIMESTAMP=$(date +%Y%m%d_%H%M%S)
                                docker cp ${BACKEND_CONTAINER}:${JSON_BACKUP_PATH} ${JSON_BACKUP_DIR}/${JSON_BACKUP_PREFIX}$TIMESTAMP.json
                                
                                # Create symlink to latest
                                ln -sf ${JSON_BACKUP_DIR}/${JSON_BACKUP_PREFIX}$TIMESTAMP.json ${JSON_BACKUP_DIR}/${JSON_LATEST}
                                
                                # Keep only last N backups
                                ls -t ${JSON_BACKUP_DIR}/${JSON_BACKUP_PREFIX}*.json 2>/dev/null | tail -n +$((${JSON_MAX_COUNT}+1)) | xargs -r rm
                                
                                echo "✅ JSON backup saved: ${JSON_BACKUP_PREFIX}$TIMESTAMP.json (${FILE_SIZE} bytes)"
                                echo "✅ Symlink updated: ${JSON_LATEST} -> ${JSON_BACKUP_PREFIX}$TIMESTAMP.json"
                            else
                                echo "⚠️ JSON file empty or missing in container ($FILE_SIZE bytes) - preserving existing backup"
                                # Don't overwrite good backup with empty file (VM restart scenario protection)
                            fi
                            
                            # Show available backups
                            echo "📁 Available backups:"
                            ls -lh ${JSON_BACKUP_DIR}/${JSON_BACKUP_PREFIX}*.json 2>/dev/null || echo "No backups yet"
                        else
                            echo "ℹ️ No running backend container - skipping JSON backup"
                        fi
                    '''
                    
                    // Backup logs directory (inside container, not volume mounted)
                    sh '''
                        # Check if backend container is running
                        if docker ps --format '{{.Names}}' | grep -q "${BACKEND_CONTAINER}"; then
                            echo "📋 Backing up logs from running container..."
                            mkdir -p ${LOGS_BACKUP_DIR}
                            
                            # Copy logs from container
                            docker cp ${BACKEND_CONTAINER}:${LOGS_DIR_CONTAINER}/. ${LOGS_BACKUP_DIR}/ 2>/dev/null || echo "No logs to backup"
                            echo "✅ Logs backed up to ${LOGS_BACKUP_DIR}/"
                        else
                            echo "ℹ️ No running backend container - skipping logs backup"
                        fi
                    '''
                    
                    // Force clean any leftover files (especially Docker-created logs with different permissions)
                    sh '''
                        if [ -d "transport-request-form-app" ]; then
                            echo "Cleaning leftover directory..."
                            # Use Docker to remove files created by Docker containers (avoids permission issues)
                            docker run --rm -v "$(pwd)/transport-request-form-app:/tmp/cleanup" alpine rm -rf /tmp/cleanup || true
                            # Fallback: try normal removal
                            rm -rf transport-request-form-app || true
                        fi
                    '''
                    withCredentials([gitUsernamePassword(credentialsId: 'c5526276-84a5-4328-9968-b0ff64ea094f', gitToolName: 'git-tool')]) {
                        sh 'git clone https://github.com/your-org/transport-request-form-app.git'
                        dir('transport-request-form-app') {
                            sh "git checkout ${params.BRANCH}"
                            // Show current commit for debugging
                            sh 'echo "=== Current commit ==="'
                            sh 'git log --oneline -3'
                        }
                    }
                    
                    // Restore JSON backup and logs directories after checkout
                    sh '''
                        # Restore logs directory (if exists from previous backup)
                        if [ -d "${LOGS_BACKUP_DIR}" ]; then
                            echo "📋 Logs will be restored to container after deploy..."
                        else
                            echo "ℹ️ No logs backup found (first deploy?)"
                        fi
                        
                        # JSON backup will be restored after container starts (see Health Check stage)
                        if [ -f "${JSON_BACKUP_DIR}/${JSON_LATEST}" ]; then
                            echo "📁 JSON backup will be restored to container after deploy..."
                            echo "📊 Latest backup info:"
                            ls -lh ${JSON_BACKUP_DIR}/${JSON_LATEST}
                        else
                            echo "ℹ️ No JSON backup found (first deploy?)"
                        fi
                    '''
                }
            }
        }
        
        stage('Action Decision') {
            steps {
                script {
                    dir('transport-request-form-app') {
                        if (params.ACTION == 'shutdown') {
                            echo '🛑 SHUTDOWN MODE - Stopping application...'
                            sh 'docker compose -f docker-compose.yaml down'
                            
                            // Cleanup sensitive files
                            sh 'rm -f .env || true'
                            echo '🧹 Cleaned up .env file'
                            
                            echo '✅ Application stopped successfully'
                            echo '🔍 Application is now offline on port 8010 (backend) and 8000 (frontend)'
                            
                            // Skip all other stages for shutdown
                            currentBuild.result = 'SUCCESS'
                            return
                        } else {
                            echo '🚀 DEPLOY MODE - Proceeding with deployment...'
                        }
                    }
                }
            }
        }
        
        stage('Setup Certificates') {
            when {
                allOf {
                    expression { params.USE_CUSTOM_CERTS == true }
                    expression { params.ACTION == 'deploy' }
                }
            }
            steps {
                script {
                    dir('transport-request-form-app') {
                        echo '🔐 Setting up custom SSL certificates...'
                        
                        // Create cert directory
                        sh 'mkdir -p backend/cert'
                        
                        // Check if certificates should be uploaded (only when USE_CUSTOM_CERTS=true)
                        if (params.USE_CUSTOM_CERTS && params.SSL_CERT && params.SSL_KEY) {
                            sh 'cp "${WORKSPACE}/${params.SSL_CERT}" backend/cert/europe.crt'
                            sh 'cp "${WORKSPACE}/${params.SSL_KEY}" backend/cert/europe.key'
                            sh 'chmod 600 backend/cert/europe.key'
                            sh 'chmod 644 backend/cert/europe.crt'
                            
                            // Save certificates to persistent location for future builds
                            sh 'mkdir -p /tmp/jenkins-ssl-certs'
                            sh 'cp backend/cert/europe.crt /tmp/jenkins-ssl-certs/'
                            sh 'cp backend/cert/europe.key /tmp/jenkins-ssl-certs/'
                            echo '✅ SSL certificates uploaded and saved for future builds'
                        } else {
                            // Try to use previously saved certificates
                            if (sh(script: 'test -f /tmp/jenkins-ssl-certs/europe.crt && test -f /tmp/jenkins-ssl-certs/europe.key', returnStatus: true) == 0) {
                                sh 'cp /tmp/jenkins-ssl-certs/europe.crt backend/cert/'
                                sh 'cp /tmp/jenkins-ssl-certs/europe.key backend/cert/'
                                sh 'chmod 600 backend/cert/europe.key'
                                sh 'chmod 644 backend/cert/europe.crt'
                                echo '✅ Using previously saved SSL certificates'
                            } else {
                                echo '⚠️ No certificates found - will run HTTP only'
                            }
                        }
                        
                        // Configure Dockerfile based on certificate availability
                        if (sh(script: 'test -f backend/cert/europe.crt && test -f backend/cert/europe.key', returnStatus: true) == 0) {
                            // SSL available - use HTTPS
                            sh '''
                                sed 's|CMD \\["uvicorn".*\\]|CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--ssl-keyfile", "./cert/europe.key", "--ssl-certfile", "./cert/europe.crt"]|' backend/Dockerfile > backend/Dockerfile.tmp
                                mv backend/Dockerfile.tmp backend/Dockerfile
                            '''
                            echo '🔒 Backend configured for HTTPS (port 8010 externally)'
                        } else {
                            // No SSL - use HTTP
                            sh '''
                                sed 's|CMD \\["uvicorn".*\\]|CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]|' backend/Dockerfile > backend/Dockerfile.tmp
                                mv backend/Dockerfile.tmp backend/Dockerfile
                            '''
                            echo '🔓 Backend configured for HTTP only (port 8010 externally)'
                        }
                        
                        echo '✅ Certificates configured successfully'
                        sh 'ls -la backend/cert/'
                    }
                }
            }
        }
        
        stage('Clean Docker Cache') {
            when {
                allOf {
                    expression { params.FORCE_REBUILD == true }
                    expression { params.ACTION == 'deploy' }
                }
            }
            steps {
                dir('transport-request-form-app') {
                    echo 'Cleaning Docker cache...'
                    // SAFE: Only clean project-specific containers and images
                    sh 'docker compose -f docker-compose.yaml down --volumes || true'
                    sh 'docker compose -f docker-compose.yaml build --no-cache --pull || true'
                    echo 'Safe cleanup completed - only project resources affected'
                }
            }
        }
        
        stage('Build Docker Image') {
            when {
                expression { params.ACTION == 'deploy' }
            }
            steps {
                dir('transport-request-form-app') {
                    script {
                        if (params.FORCE_REBUILD) {
                            echo 'Force rebuilding everything without cache...'
                            sh 'docker compose -f docker-compose.yaml build --no-cache'
                        } else {
                            echo 'Rebuilding frontend without cache, backend with cache...'
                            sh 'docker compose -f docker-compose.yaml build --no-cache frontend'
                            sh 'docker compose -f docker-compose.yaml build backend'
                        }
                    }
                }
            }
        }
        
        stage('Stop Running Container') {
            when {
                expression { params.ACTION == 'deploy' }
            }
            steps {
                dir('transport-request-form-app') {
                    sh 'docker compose -f docker-compose.yaml down'
                }
            }
        }
        
        stage('Run Docker Container') {
            when {
                expression { params.ACTION == 'deploy' }
            }
            steps {
                dir('transport-request-form-app') {
                    script {
                        // Get debug secret key (optional)
                        def debugKey = params.DEBUG_SECRET_KEY ? params.DEBUG_SECRET_KEY.toString().trim() : ''
                        
                        // Choose token source: Token Manager (recommended) or Manual token (legacy)
                        if (params.USE_TOKEN_MANAGER) {
                            echo '🔄 Using Token Manager - fetching RPA bot credentials...'
                            
                            // Get webapp credentials from Jenkins Credentials Store
                            withCredentials([usernamePassword(
                                credentialsId: 'webapp-transport-app',
                                usernameVariable: 'RPA_BOT_EMAIL',
                                passwordVariable: 'RPA_BOT_PASSWORD'
                            )]) {
                                // Create .env with RPA bot password (Token Manager will fetch token automatically)
                                // Using concatenation to avoid Groovy String interpolation security warning
                                def envContent = 'RPA_BOT_PASSWORD=' + RPA_BOT_PASSWORD + '\n'
                                envContent += 'SHAREPOINT_ACCESS_TOKEN=\n'  // Empty - will be fetched by Token Manager
                                
                                if (debugKey && debugKey != '') {
                                    envContent += 'DEBUG_SECRET_KEY=' + debugKey + '\n'
                                    echo '🔐 Debug mode will be available with secret key'
                                }
                                
                                writeFile file: '.env', text: envContent
                                echo '✅ .env file created with RPA bot credentials (Token Manager enabled)'
                                echo '✅ RPA Email: ' + RPA_BOT_EMAIL
                            }
                        } else {
                            echo '⚠️ Using MANUAL token mode (legacy) - Token Manager disabled'
                            
                            // Legacy mode: manual SharePoint token
                            def token = params.MANUAL_SHAREPOINT_TOKEN?.trim()
                            if (!token || token == '') {
                                error('❌ ERROR: MANUAL_SHAREPOINT_TOKEN is REQUIRED when Token Manager is disabled!')
                            }
                            
                            // Create .env file with manual token
                            // Using concatenation to avoid Groovy String interpolation security warning
                            def envContent = 'SHAREPOINT_ACCESS_TOKEN=' + token + '\n'
                            envContent += 'RPA_BOT_PASSWORD=\n'  // Empty - not used in manual mode
                            
                            if (debugKey && debugKey != '') {
                                envContent += 'DEBUG_SECRET_KEY=' + debugKey + '\n'
                            }
                            
                            writeFile file: '.env', text: envContent
                            
                            echo '✅ .env file created with manual SharePoint token'
                            
                            // Verify token format
                            if (!token.startsWith('eyJ')) {
                                echo '⚠️ WARNING: Token does not start with "eyJ" - may be invalid JWT token'
                            }
                            
                            echo "✅ Token length: ${token.length()} characters"
                            echo "✅ Token preview: ${token.take(50)}..."
                        }
                    }
                    
                    sh 'docker compose -f docker-compose.yaml up -d'
                    
                    // Wait for containers to start
                    echo 'Waiting for containers to start...'
                    sh 'sleep 10'
                    
                    // Verify containers are running
                    echo 'Checking container status...'
                    sh 'docker compose -f docker-compose.yaml ps'
                    
                    // Verify credentials in container
                    script {
                        if (params.USE_TOKEN_MANAGER) {
                            echo 'Verifying RPA bot password in container (Token Manager mode)...'
                            sh 'docker exec ${BACKEND_CONTAINER} sh -c "[ -n \\"\\$RPA_BOT_PASSWORD\\" ] && echo \\"✅ RPA_BOT_PASSWORD is set\\" || echo \\"❌ RPA_BOT_PASSWORD not found\\""'
                        } else {
                            echo 'Verifying SharePoint token in container (Manual mode)...'
                            sh 'docker exec ${BACKEND_CONTAINER} sh -c "echo \\$SHAREPOINT_ACCESS_TOKEN | head -c 50" || echo "⚠️ Token verification failed"'
                        }
                    }
                }
            }
        }
        
        stage('Health Check') {
            when {
                expression { params.ACTION == 'deploy' }
            }
            steps {
                dir('transport-request-form-app') {
                    script {
                        echo 'Running simplified health checks...'
                        
                        // Basic container status  
                        sh '''
                            echo "=== Container Status ==="
                            docker ps --filter name=${BACKEND_CONTAINER}
                            docker ps --filter name=${FRONTEND_CONTAINER}
                            echo ""
                            
                            echo "=== Backend Logs (last 30 lines) ==="
                            docker logs ${BACKEND_CONTAINER} --tail 30
                            echo ""
                            
                            echo "=== Logger Initialization Diagnostics ==="
                            docker logs ${BACKEND_CONTAINER} 2>&1 | grep -E "✅|⚠️|❌|Log directory|handler" || echo "⚠️ No logger diagnostic messages found in logs"
                            echo ""
                        '''
                        
                        // Essential health checks
                        sh '''
                            echo "=== Essential Health Checks ==="
                            
                            # Test backend API health
                            echo "Testing backend API health (port ${BACKEND_PORT}):"
                            if curl -f -s -m 10 http://${SERVER_HOST}:${BACKEND_PORT}/api/health >/dev/null 2>&1; then
                                echo "✅ Backend API (port ${BACKEND_PORT}) - OK"
                            else
                                echo "❌ Backend API (port ${BACKEND_PORT}) - FAIL"
                                exit 1
                            fi
                            
                            # Test frontend access
                            echo "Testing frontend access (port ${FRONTEND_PORT}):"
                            if curl -f -s -m 10 http://${SERVER_HOST}:${FRONTEND_PORT} >/dev/null 2>&1; then
                                echo "✅ Frontend (port ${FRONTEND_PORT}) - OK"
                            else
                                echo "❌ Frontend (port 8002) - FAIL"
                                exit 1
                            fi
                            
                            # Skipping external domain health check temporarily
                            echo "Skipping external domain health check (not configured yet)"
                            # echo "Testing external domain (optional):"
                            # if curl -f -s -m 10 -k https://transport-app.yourdomain.com/api/health >/dev/null 2>&1; then
                            #     echo "✅ External domain - OK"
                            # else
                            #     echo "⚠️  External domain - Not configured (requires VM admin nginx setup)"
                            # fi
                        '''
                        
                        // Test API functionality with one simple request
                        sh '''
                            echo "=== API Functionality Test ==="
                            
                            # Skipping API submit functionality test temporarily
                            echo "Skipping API submit functionality test (external domain not configured)"
                            # echo "Testing API submit via external domain:"
                            # RESPONSE=$(curl -f -s -m 15 -k -X POST https://transport-app.yourdomain.com/api/submit \
                            #     -F 'data={"deliveryNoteNumber":"JENKINS-TEST","truckLicensePlates":"TEST-123","trailerLicensePlates":"TEST-456","carrierCountry":"Austria","carrierTaxCode":"TAX123","carrierFullName":"Jenkins Test","borderCrossing":"Petea","borderCrossingDate":"2025-11-01"}' 2>/dev/null || echo "FAIL")
                            # if echo "$RESPONSE" | grep -q "request_id"; then
                            #     echo "✅ API Submit functionality - OK"
                            #     echo "   Response contains request_id: $(echo "$RESPONSE" | grep -o 'REQ-[^"']*')"
                            # else
                            #     echo "❌ API Submit functionality - FAIL"
                            #     echo "   Response: $RESPONSE"
                            # fi
                        '''
                        
                        // Restore JSON backup and logs to container
                        sh '''
                            echo "=== Restoring Data to Container ==="
                            
                            # Wait for container to be fully ready
                            sleep 5
                            
                            # Restore JSON backup to container
                            if [ -f "${JSON_BACKUP_DIR}/${JSON_LATEST}" ]; then
                                echo "♻️ Restoring JSON backup to container..."
                                
                                # Resolve symlink to actual file (docker cp doesn't follow symlink chains)
                                ACTUAL_FILE=$(readlink -f ${JSON_BACKUP_DIR}/${JSON_LATEST})
                                echo "📁 Actual backup file: $ACTUAL_FILE"
                                
                                # Copy actual file (not symlink)
                                docker cp $ACTUAL_FILE ${BACKEND_CONTAINER}:${JSON_BACKUP_PATH}
                                
                                # Fix permissions and ownership (ensure writable by container user)
                                docker exec ${BACKEND_CONTAINER} chmod 666 ${JSON_BACKUP_PATH}
                                docker exec ${BACKEND_CONTAINER} chown $(docker exec ${BACKEND_CONTAINER} id -u):$(docker exec ${BACKEND_CONTAINER} id -g) ${JSON_BACKUP_PATH} || true
                                
                                # Verify restore
                                RESTORED_SIZE=$(docker exec ${BACKEND_CONTAINER} stat -c%s ${JSON_BACKUP_PATH} 2>/dev/null || echo 0)
                                echo "✅ JSON backup restored to container ($RESTORED_SIZE bytes)"
                            else
                                echo "ℹ️ No JSON backup to restore (first deploy - will be created on first submit)"
                            fi
                            
                            # Restore logs to container
                            if [ -d "${LOGS_BACKUP_DIR}" ] && [ "$(ls -A ${LOGS_BACKUP_DIR} 2>/dev/null)" ]; then
                                echo "📋 Restoring logs to container..."
                                docker cp ${LOGS_BACKUP_DIR}/. ${BACKEND_CONTAINER}:${LOGS_DIR_CONTAINER}/
                                echo "✅ Logs restored to container"
                            else
                                echo "ℹ️ No logs to restore (first deploy - will be created by application)"
                            fi
                        '''
                    }
                }
            }
        }
    }
    
    post {
        always {
            script {
                dir('transport-request-form-app') {
                    echo 'Pipeline completed.'
                    // Cleanup sensitive files
                    sh 'rm -f .env || true'
                }
                
                // Clean workspace using Docker (avoids permission issues with Docker-created files)
                echo '🧹 Cleaning workspace...'
                sh '''
                    if [ -d "transport-request-form-app" ]; then
                        # Use Docker to remove files created by Docker containers
                        docker run --rm -v "$(pwd)/transport-request-form-app:/tmp/cleanup" alpine rm -rf /tmp/cleanup || true
                        # Fallback: try normal removal for remaining files
                        rm -rf transport-request-form-app || true
                    fi
                '''
                echo '✅ Workspace cleaned'
            }
            // Clean workspace
            // deleteDir()
        }
        failure {
            script {
                echo 'Pipeline failed! Collecting debug information...'
                sh '''
                    echo "=== DEBUG INFO ==="
                    docker ps -a
                    echo ""
                    echo "=== Backend Logs ==="
                    docker logs ${BACKEND_CONTAINER} --tail 50 || echo "No backend logs"
                    echo ""
                    echo "=== Frontend Logs ==="
                    docker logs ${FRONTEND_CONTAINER} --tail 50 || echo "No frontend logs"
                '''
            }
        }
        
        success {
            echo '🚀 Deployment successful!'
            echo "🌐 Frontend: http://${SERVER_HOST}:${FRONTEND_PORT}"
            echo "🔧 Backend API: http://${SERVER_HOST}:${BACKEND_PORT}/docs"
            echo '🌍 External access: https://transport-app.yourdomain.com'
        }
        
        unstable {
            echo '⚠️  Deployment completed with warnings.'
        }
    }
}