@echo off
echo Setting up Python virtual environment for Scryfall scraper...
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error creating virtual environment. Make sure Python is installed.
    pause
    exit /b 1
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing required packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing packages.
    pause
    exit /b 1
)

echo.
echo Running the scraper...
python scrape_functional_tags.py

echo.
echo Done! Check the functional_tags.json file for results.
pause
