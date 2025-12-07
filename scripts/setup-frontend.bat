@echo off
REM Agent47 Frontend Setup Script for Windows
REM This script sets up the frontend for local development

echo 🎨 Setting up Agent47 Frontend...

REM Check if we're in the right directory
if not exist "frontend\package.json" (
    echo [ERROR] Please run this script from the Agent47 root directory
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js 18+ first.
    echo [INFO] Download from: https://nodejs.org/
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

for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo [SUCCESS] npm %NPM_VERSION% detected

REM Navigate to frontend directory
cd frontend

REM Check if package.json exists
if not exist "package.json" (
    echo [ERROR] package.json not found in frontend directory
    exit /b 1
)

echo [INFO] Found package.json with dependencies

REM Install dependencies
echo [INFO] Installing dependencies...
npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [SUCCESS] Dependencies installed successfully

REM Check if .env.local exists
if not exist ".env.local" (
    echo [WARNING] .env.local file not found. Creating from template...
    if exist ".env.example" (
        copy ".env.example" ".env.local" >nul
        echo [SUCCESS] Created .env.local file from template
        echo [WARNING] Please edit .env.local file with your actual configuration values
    ) else (
        echo [WARNING] No .env.example found. Creating basic .env.local...
        (
            echo # Agent47 Frontend Environment Variables
            echo NEXT_PUBLIC_API_URL=http://localhost:8000
            echo NEXT_PUBLIC_WS_URL=ws://localhost:8000
            echo NEXT_PUBLIC_DEBUG=true
            echo NODE_ENV=development
            echo.
            echo # AI Services
            echo NEXT_PUBLIC_CHUTES_API_URL=https://api.chutes.ai
            echo NEXT_PUBLIC_GROK_API_URL=http://localhost:8001
            echo.
            echo # Feature Flags
            echo NEXT_PUBLIC_ENABLE_ANALYTICS=true
            echo NEXT_PUBLIC_ENABLE_CHAT=true
            echo NEXT_PUBLIC_ENABLE_VOICE=true
        ) > .env.local
        echo [SUCCESS] Created basic .env.local file
    )
) else (
    echo [SUCCESS] .env.local file already exists
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

REM Run type check
echo [INFO] Running TypeScript type check...
npx tsc --noEmit
if %errorlevel% equ 0 (
    echo [SUCCESS] TypeScript type check passed
) else (
    echo [WARNING] TypeScript type check failed. Please fix type errors.
)

REM Run linting
echo [INFO] Running ESLint...
npm run lint
if %errorlevel% equ 0 (
    echo [SUCCESS] ESLint check passed
) else (
    echo [WARNING] ESLint found issues. Please fix them.
)

REM Go back to root directory
cd ..

echo [SUCCESS] Frontend setup completed!
echo.
echo [INFO] Next steps:
echo 1. Edit frontend\.env.local with your configuration
echo 2. Start the backend: scripts\dev-backend.bat
echo 3. Start the frontend: scripts\dev-frontend.bat
echo 4. Open http://localhost:3000 in your browser
echo.
echo [INFO] Available commands:
echo   scripts\dev-frontend.bat    # Start frontend development server
echo   scripts\dev-backend.bat     # Start backend development server
echo   scripts\start.bat           # Start full platform with Docker
echo.
echo [SUCCESS] Happy coding! 🎉
