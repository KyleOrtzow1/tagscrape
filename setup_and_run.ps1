# PowerShell script to set up virtual environment and run the scraper
Write-Host "Setting up Python virtual environment for Scryfall scraper..." -ForegroundColor Green
Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error creating virtual environment. Make sure Python is installed." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing packages." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Running the scraper..." -ForegroundColor Yellow
python scrape_functional_tags.py

Write-Host ""
Write-Host "Done! Check the functional_tags.json file for results." -ForegroundColor Green
Read-Host "Press Enter to exit"
