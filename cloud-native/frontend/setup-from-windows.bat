@echo off
echo ========================================
echo Metlab.edu Frontend Setup (via WSL)
echo ========================================
echo.
echo This script will run the setup from within WSL...
echo.

wsl bash -c "cd /home/metrix/git/Metlab.edu/cloud-native/frontend && chmod +x setup.sh && ./setup.sh"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Setup Complete!
    echo ========================================
    echo.
    echo To start the development server, run:
    echo   wsl bash -c "cd /home/metrix/git/Metlab.edu/cloud-native/frontend && npm run dev"
    echo.
    echo Or open a WSL terminal and run:
    echo   cd /home/metrix/git/Metlab.edu/cloud-native/frontend
    echo   npm run dev
    echo.
) else (
    echo.
    echo ========================================
    echo Setup Failed!
    echo ========================================
    echo.
    echo Please open a WSL terminal and run:
    echo   cd /home/metrix/git/Metlab.edu/cloud-native/frontend
    echo   ./setup.sh
    echo.
)

pause
