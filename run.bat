@echo off
echo ========================================
echo   CodeMind - Starting Application
echo ========================================
echo.

cd backend

echo Checking for .env file...
if not exist .env (
    echo.
    echo WARNING: .env file not found!
    echo Please create backend/.env with:
    echo GEMINI_API_KEY=your_api_key_here
    echo.
    echo Get your FREE API key at: https://makersuite.google.com/app/apikey
    echo.
    pause
)

echo.
echo Starting Flask server...
echo.
echo Open your browser to: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause

