# Python Installation Helper Script for Windows
# This script helps you install Python on Windows

Write-Host "Python Installation Helper" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host ""

# Check if Python is already installed
$pythonInstalled = $false
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python is already installed: $pythonVersion" -ForegroundColor Green
        $pythonInstalled = $true
    }
} catch {
    # Python not found, continue
}

if (-not $pythonInstalled) {
    Write-Host "Python is not installed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install Python using one of these methods:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Method 1: Download from python.org (Recommended)" -ForegroundColor White
    Write-Host "  1. Go to: https://www.python.org/downloads/" -ForegroundColor Gray
    Write-Host "  2. Download the latest Python 3.x" -ForegroundColor Gray
    Write-Host "  3. Run the installer" -ForegroundColor Gray
    Write-Host "  4. IMPORTANT: Check 'Add Python to PATH'" -ForegroundColor Yellow
    Write-Host "  5. Click 'Install Now'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Method 2: Microsoft Store" -ForegroundColor White
    Write-Host "  1. Open Microsoft Store" -ForegroundColor Gray
    Write-Host "  2. Search for 'Python 3.12'" -ForegroundColor Gray
    Write-Host "  3. Click Install" -ForegroundColor Gray
    Write-Host ""
    Write-Host "After installation:" -ForegroundColor Cyan
    Write-Host "  1. Close and reopen this terminal" -ForegroundColor Yellow
    Write-Host "  2. Run: python --version" -ForegroundColor Gray
    Write-Host "  3. Then you can start the backend with: python backend\main.py" -ForegroundColor Gray
    Write-Host ""
    
    # Try to open Python download page
    $openBrowser = Read-Host "Would you like to open the Python download page? (y/n)"
    if ($openBrowser -eq 'y' -or $openBrowser -eq 'Y') {
        Start-Process "https://www.python.org/downloads/"
    }
} else {
    Write-Host ""
    Write-Host "Python is ready to use!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To start the backend server, run:" -ForegroundColor Cyan
    Write-Host "  cd backend" -ForegroundColor White
    Write-Host "  python main.py" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use the provided script:" -ForegroundColor Cyan
    Write-Host "  .\scripts\dev-backend.bat" -ForegroundColor White
}

