@echo off
echo ========================================
echo Starting Metlab.edu Frontend (via WSL)
echo ========================================
echo.
echo Starting development server...
echo The app will be available at http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

wsl bash -c "cd /home/metrix/git/Metlab.edu/cloud-native/frontend && npm run dev"
