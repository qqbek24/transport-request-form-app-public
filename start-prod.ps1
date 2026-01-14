# Production without nginx container
Write-Host "Starting production environment (direct ports)..." -ForegroundColor Yellow
docker-compose -f docker-compose.yaml up --build