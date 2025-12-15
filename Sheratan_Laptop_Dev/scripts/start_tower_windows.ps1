Set-Location (Split-Path $PSScriptRoot)\docker
if (-not (Test-Path .env)) { Copy-Item .env.example .env; Write-Host "Created .env - edit if needed." -ForegroundColor Yellow }
docker compose up -d --build
docker compose ps
Write-Host "Logs: docker compose logs -f" -ForegroundColor Cyan
