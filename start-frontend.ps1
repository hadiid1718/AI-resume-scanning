# Start the Streamlit frontend from the project root.
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

Write-Host "Installing dependencies..." -ForegroundColor Cyan
& $python -m pip install -r (Join-Path $ProjectRoot "requirements.txt") -q
& $python -m pip install -e . -q

Write-Host "Starting frontend on http://localhost:8501" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
& $python (Join-Path $ProjectRoot "frontend\run.py")
