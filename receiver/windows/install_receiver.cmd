@echo off
setlocal

net session >nul 2>&1
if not "%errorlevel%"=="0" (
    echo Requesting Administrator permission...
    powershell.exe -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo Installing the PiDrop Windows receiver...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_receiver.ps1"

echo.
if not "%errorlevel%"=="0" (
    echo Installation failed. Read the error shown above.
) else (
    echo Installation completed successfully.
)
echo.
pause
