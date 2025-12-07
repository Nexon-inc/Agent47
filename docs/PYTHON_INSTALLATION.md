# Python Installation Guide for Windows

## Quick Installation Methods

### Method 1: Download from Python.org (Recommended)

1. **Download Python:**
   - Go to https://www.python.org/downloads/
   - Click "Download Python 3.x.x" (latest version)
   - The installer will download automatically

2. **Run the Installer:**
   - Double-click the downloaded `.exe` file
   - **IMPORTANT:** Check the box "Add Python to PATH" at the bottom of the installer
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation:**
   - Open a new PowerShell window (close and reopen)
   - Run: `python --version`
   - You should see something like: `Python 3.12.x`

### Method 2: Using Microsoft Store

1. Open Microsoft Store
2. Search for "Python 3.12" or "Python 3.11"
3. Click "Install"
4. Once installed, open a new PowerShell window
5. Run: `python --version` to verify

### Method 3: Using Chocolatey (if you have it)

```powershell
choco install python
```

## After Installation

1. **Close and reopen your PowerShell/terminal** (required for PATH to update)

2. **Verify Python is installed:**
   ```powershell
   python --version
   ```

3. **Verify pip is installed:**
   ```powershell
   pip --version
   ```

## Starting the Backend Server

Once Python is installed, you can start the backend server:

```powershell
cd backend
python main.py
```

Or use the provided script:
```powershell
.\scripts\dev-backend.bat
```

## Troubleshooting

### "python is not recognized"
- Make sure you checked "Add Python to PATH" during installation
- Close and reopen your terminal/PowerShell
- Restart your computer if the issue persists
- Manually add Python to PATH:
  1. Search for "Environment Variables" in Windows
  2. Edit "Path" variable
  3. Add: `C:\Users\YourUsername\AppData\Local\Programs\Python\Python3xx\`
  4. Add: `C:\Users\YourUsername\AppData\Local\Programs\Python\Python3xx\Scripts\`

### Using Python Launcher
If `python` doesn't work, try:
```powershell
py main.py
```

The `py` launcher is usually installed with Python on Windows.

