# Script to add Python to PATH
Write-Host "Adding Python to PATH..." -ForegroundColor Green

$pythonPath = "$env:LOCALAPPDATA\Programs\Python\Python313"
$pythonScriptsPath = "$pythonPath\Scripts"

# Check if Python exists
if (Test-Path "$pythonPath\python.exe") {
    Write-Host "Found Python at: $pythonPath" -ForegroundColor Green
    
    # Get current PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    
    # Check if already in PATH
    if ($currentPath -notlike "*$pythonPath*") {
        # Add Python to user PATH
        $newPath = "$currentPath;$pythonPath;$pythonScriptsPath"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        
        Write-Host "Python has been added to PATH!" -ForegroundColor Green
        Write-Host "Please restart your terminal/PowerShell for changes to take effect." -ForegroundColor Yellow
        
        # Update current session PATH
        $env:Path += ";$pythonPath;$pythonScriptsPath"
        Write-Host "`nCurrent session PATH updated. Testing Python..." -ForegroundColor Cyan
        
        # Test Python
        & "$pythonPath\python.exe" --version
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`nPython is now accessible! You can use 'python' command." -ForegroundColor Green
        }
    } else {
        Write-Host "Python is already in PATH!" -ForegroundColor Yellow
        & "$pythonPath\python.exe" --version
    }
} else {
    Write-Host "Python not found at expected location: $pythonPath" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
}

