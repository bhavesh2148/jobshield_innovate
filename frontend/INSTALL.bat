@echo off
REM JobShield Frontend Installation Script

echo.
echo ========================================
echo   JobShield - Installing dependencies
echo ========================================
echo.

REM Install dependencies
echo Installing npm packages (including framer-motion)...
call npm install

echo.
echo ========================================
echo   Installation complete!
echo ========================================
echo.
echo To start the development server, run:
echo    npm run dev
echo.
echo Make sure the backend is running at http://localhost:8000
echo.
echo Features:
echo   - Login page with fake auth
echo   - Landing page with ripple grid effect
echo   - Light/Dark theme toggle
echo   - Smooth page transitions
echo   - Fully responsive design
echo.
echo Happy coding!
echo.
pause
