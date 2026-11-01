# ──────────────────────────────────────────
# start.ps1  –  one-command launch script
# ──────────────────────────────────────────
Set-Location $PSScriptRoot

# 1. Create venv if missing
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

# 2. Activate
& .\venv\Scripts\Activate.ps1

# 3. Install deps
Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet

# 4. Load .env if present
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.+)") {
            $env:($matches[1].Trim()) = $matches[2].Trim()
        }
    }
}

# 5. Launch
Write-Host ""
Write-Host "  Chatbot running at http://localhost:8000" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
