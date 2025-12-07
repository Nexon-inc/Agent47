@echo off
REM Agent47 Frontend Development Script for Windows
REM This script starts the frontend server for local development

echo 🚀 Starting Agent47 Frontend for Development...

REM Check if we're in the right directory
if not exist "frontend\package.json" (
    echo [ERROR] Please run this script from the Agent47 root directory
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js 18+ first.
    exit /b 1
)

REM Check Node.js version
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [SUCCESS] Node.js %NODE_VERSION% detected

REM Check if npm is installed
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed. Please install npm first.
    exit /b 1
)

REM Check if dependencies are installed
if not exist "frontend\node_modules" (
    echo [INFO] Installing dependencies...
    cd frontend
    npm install
    cd ..
    echo [SUCCESS] Dependencies installed
) else (
    echo [INFO] Dependencies already installed
)

REM Check if .env.local exists
if not exist "frontend\.env.local" (
    echo [WARNING] .env.local file not found. Creating from template...
    if exist "frontend\.env.example" (
        copy "frontend\.env.example" "frontend\.env.local" >nul
        echo [SUCCESS] Created .env.local file from template
        echo [WARNING] Please edit frontend\.env.local file with your actual configuration values
    ) else (
        echo [WARNING] No .env.example found. Using default configuration
    )
) else (
    echo [SUCCESS] .env.local file found
)

REM Check if backend is running
echo [INFO] Checking backend connection...
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Backend is running on http://localhost:8000
) else (
    echo [WARNING] Backend is not running on http://localhost:8000
    echo [INFO] Make sure to start the backend server first with: scripts\dev-backend.bat
)

REM Start the frontend server
echo [INFO] Starting Agent47 Frontend server...
echo [INFO] Frontend will be available at: http://localhost:3000
echo [INFO] Press Ctrl+C to stop the server
echo.

cd frontend
npm run dev
