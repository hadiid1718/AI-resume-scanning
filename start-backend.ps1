# Start the FastAPI backend from the project root.
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

Write-Host "Installing project package (editable)..." -ForegroundColor Cyan
& $python -m pip install -e . -q

Write-Host "Starting backend on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
& $python (Join-Path $ProjectRoot "backend\run.py")
