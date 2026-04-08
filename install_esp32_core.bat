@echo off
echo ========================================================
echo       ESP32 Arduino Core - Manual Installer
echo ========================================================
echo.
echo This script will install the ESP32 files directly from GitHub
echo to bypass the broken Arduino IDE Boards Manager downloader.
echo.

set TARGET_DIR=%USERPROFILE%\Documents\Arduino\hardware\espressif
set TARGET_REPO=%TARGET_DIR%\esp32

if not exist "%TARGET_DIR%" (
    echo [1/3] Creating directory %TARGET_DIR%...
    mkdir "%TARGET_DIR%"
) else (
    echo [1/3] Directory already exists.
)

if not exist "%TARGET_REPO%" (
    echo [2/3] Cloning ESP32 repository from GitHub...
    git clone https://github.com/espressif/arduino-esp32.git "%TARGET_REPO%"
) else (
    echo [2/3] Repository already exists, pulling latest updates...
    cd "%TARGET_REPO%"
    git pull
)

echo [3/3] Downloading underlying ESP32 compiler tools...
cd "%TARGET_REPO%\tools"
call get.exe

echo.
echo ========================================================
echo   DONE! You can now restart the Arduino IDE. 
echo   The ESP32-S3 boards will automatically appear in 
echo   Tools -^> Board -^> ESP32 Arduino.
echo ========================================================
pause
