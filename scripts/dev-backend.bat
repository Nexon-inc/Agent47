@echo off
echo.
echo [Agent47] Cleaning Python cache...

REM Find and remove all __pycache__ directories from the project root
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        echo Deleting: %%d
        rd /s /q "%%d"
    )
)

echo.
echo [Agent47] Starting backend server in development mode...
cd backend
py -3.12 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload