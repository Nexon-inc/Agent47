@echo off
REM Agent47 Startup Script for Windows
REM This script starts the entire Agent47 platform

echo 🚀 Starting Agent47 Multi-Agent AI Platform...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

echo [SUCCESS] Docker and Docker Compose are installed

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found. Creating from template...
    if exist env.example (
        copy env.example .env >nul
        echo [SUCCESS] Created .env file from template
        echo [WARNING] Please edit .env file with your actual configuration values
    ) else (
        echo [ERROR] env.example file not found. Cannot create .env file.
        exit /b 1
    )
) else (
    echo [SUCCESS] .env file found
)

REM Start services with Docker Compose
echo [INFO] Starting services with Docker Compose...

echo [INFO] Pulling latest Docker images...
docker-compose pull

echo [INFO] Building custom Docker images...
docker-compose build

echo [INFO] Starting all services...
docker-compose up -d

echo [SUCCESS] All services started successfully!

REM Wait for services to be ready
echo [INFO] Waiting for services to be ready...

echo [INFO] Waiting for PostgreSQL...
:wait_postgres
docker-compose exec -T postgres pg_isready -U agent47 -d agent47_db >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    goto wait_postgres
)
echo [SUCCESS] PostgreSQL is ready

echo [INFO] Waiting for Redis...
:wait_redis
docker-compose exec -T redis redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    goto wait_redis
)
echo [SUCCESS] Redis is ready

echo [INFO] Waiting for Backend API...
:wait_backend
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 5 >nul
    goto wait_backend
)
echo [SUCCESS] Backend API is ready

echo [INFO] Waiting for Frontend...
:wait_frontend
curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 5 >nul
    goto wait_frontend
)
echo [SUCCESS] Frontend is ready

REM Show service status
echo [INFO] Service Status:
docker-compose ps

echo.
echo [SUCCESS] 🎉 Agent47 Platform is now running!
echo.
echo 📱 Access Points:
echo   • Frontend:     http://localhost:3000
echo   • Backend API:  http://localhost:8000
echo   • API Docs:     http://localhost:8000/docs
echo   • Grafana:      http://localhost:3001 (admin/admin)
echo   • Prometheus:   http://localhost:9090
echo.
echo 🔧 Management Commands:
echo   • View logs:    docker-compose logs -f [service]
echo   • Stop all:     docker-compose down
echo   • Restart:      docker-compose restart [service]
echo   • Scale:        docker-compose up -d --scale backend=3
echo.

pause
