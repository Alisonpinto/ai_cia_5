@echo off
echo ================================================
echo   Cloud Agent System - Starting...
echo ================================================
echo.
echo Activating virtual environment...
if exist ..\venv\Scripts\activate.bat (
    call ..\venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
echo.
echo Installing requirements (if needed)...
pip install -r requirements.txt --quiet
echo.
echo Seeding database (if needed)...
if not exist instance\cloud_agents.db (
    python seed_data.py
)
echo.
echo Starting Flask app...
echo Open your browser at http://localhost:5000
echo Login with demo / KEY-DEMO-001
echo.
python app.py
pause
