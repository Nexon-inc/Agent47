# Script to restart Zookeeper and Kafka after Docker Desktop restart
# Run this after Docker Desktop has fully restarted

Write-Host "Restarting Zookeeper and Kafka services..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker ps > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

Write-Host "`nStep 1: Removing old containers (if they exist)..." -ForegroundColor Yellow
docker-compose rm -f zookeeper kafka 2>&1 | Out-Null

Write-Host "Step 2: Starting Zookeeper..." -ForegroundColor Yellow
docker-compose up -d zookeeper

if ($LASTEXITCODE -eq 0) {
    Write-Host "Waiting for Zookeeper to be healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host "Step 3: Starting Kafka..." -ForegroundColor Yellow
    docker-compose up -d kafka
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nWaiting for services to be healthy..." -ForegroundColor Yellow
        Start-Sleep -Seconds 15
        
        Write-Host "`nChecking service status..." -ForegroundColor Yellow
        docker-compose ps zookeeper kafka
        
        Write-Host "`nDone! Services should be running now." -ForegroundColor Green
    } else {
        Write-Host "Failed to start Kafka. Check the logs with: docker-compose logs kafka" -ForegroundColor Red
    }
} else {
    Write-Host "Failed to start Zookeeper. Check the logs with: docker-compose logs zookeeper" -ForegroundColor Red
}

