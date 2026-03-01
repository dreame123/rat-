@echo off
title Bot1 Setup

echo ================================
echo Creating bot1 folder on Desktop...
echo ================================

set DESKTOP=%USERPROFILE%\Desktop
set DOWNLOADS=%USERPROFILE%\Downloads

mkdir "%DESKTOP%\bot1" 2>nul

echo ================================
echo Copying bot1.py from Downloads...
echo ================================

copy "%DOWNLOADS%\bot1.py" "%DESKTOP%\bot1\" /Y

echo ================================
echo Moving to bot1 folder...
echo ================================

cd /d "%DESKTOP%\bot1"

echo ================================
echo Creating virtual environment...
echo ================================

python -m venv venv

echo ================================
echo Opening PowerShell with ExecutionPolicy Bypass...
echo ================================

powershell -NoExit -ExecutionPolicy Bypass -Command ^
"cd '%DESKTOP%\bot1'; ^
.\venv\Scripts\Activate.ps1; ^
python -m pip install --upgrade pip; ^
pip install requests pycryptodome sounddevice scipy numpy pillow opencv-python pyttsx3 psutil pyautogui browser-cookie3 discord.py"

pause