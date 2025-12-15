param(
  [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

Write-Host "== Sheratan Laptop Dev Launcher ==" -ForegroundColor Cyan
Write-Host "Root: $ProjectRoot"

$venv = Join-Path $ProjectRoot ".venv"
$py = Join-Path $venv "Scripts\python.exe"
$pip = Join-Path $venv "Scripts\pip.exe"

if (!(Test-Path $py)) {
  Write-Host "No venv found -> creating .venv" -ForegroundColor Yellow
  python -m venv $venv
}

Write-Host "Activating venv + installing requirements (idempotent)" -ForegroundColor Yellow
& $pip install -r (Join-Path $ProjectRoot "requirements.txt")

Write-Host "Starting UI (Streamlit) on http://localhost:8501" -ForegroundColor Green
$ui = "streamlit"
Start-Process -FilePath $py -ArgumentList "-m", $ui, "run", (Join-Path $ProjectRoot "ui\dashboard.py")

Write-Host "Starting Core CLI (optional) in this window" -ForegroundColor Green
Set-Location $ProjectRoot
& $py -m core.kernel
