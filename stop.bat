@echo off
REM Stop everything for Tloque Nahuaque (Windows)

echo Stopping Tloque Nahuaque...

REM Kill backend (python orchestrator)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING"') do taskkill /PID %%a /F 2>nul && echo Backend stopped

REM Kill frontend (node on 5173)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173.*LISTENING"') do taskkill /PID %%a /F 2>nul && echo Frontend stopped

REM Kill desktop pet
wmic process where "commandline like '%%desktop_pet.py%%'" call terminate 2>nul && echo Pet stopped

echo Done.
