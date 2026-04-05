@echo off
REM Start everything for Tloque Nahuaque (Windows)
REM Usage: start.bat

setlocal
set DIR=%~dp0

echo Starting Tloque Nahuaque...

REM 1. Create venv if missing
if not exist "%DIR%venv" (
    echo Creating virtual environment...
    python -m venv "%DIR%venv"
    call "%DIR%venv\Scripts\activate.bat"
    pip install -q -r "%DIR%requirements.txt" PyQt6 Pillow discord.py python-dotenv 2>nul
) else (
    call "%DIR%venv\Scripts\activate.bat"
)

REM 2. Start backend API (port 8000)
echo Starting backend on :8000...
start /B "" python -m orchestrator.main
timeout /t 2 /nobreak >nul

REM 3. Start frontend (port 5173)
echo Starting frontend on :5173...
cd /d "%DIR%frontend"
start /B "" npm run dev
cd /d "%DIR%"
timeout /t 2 /nobreak >nul

REM 4. Start desktop pet
echo Starting Nahua desktop pet...
start /B "" python "%DIR%desktop_pet.py"

echo.
echo All systems go!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   Pet:      Nahua is on your screen
echo.
echo To stop everything: stop.bat
