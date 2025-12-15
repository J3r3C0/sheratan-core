# =============================================
# SHERATAN CORE - TOWER MODE
# Startet alle Docker-Services auf dem Tower
# =============================================

param(
    [switch]$Build,
    [switch]$Detach
)

$ErrorActionPreference = "Stop"

Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   SHERATAN CORE - TOWER MODE           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get script directory (works on Tower local or via SMB)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check Docker
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker nicht erreichbar. Bitte Docker Desktop starten." -ForegroundColor Red
    exit 1
}

# Load .env if exists
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
    Write-Host "✓ .env geladen" -ForegroundColor Green
}

# Build if requested
if ($Build) {
    Write-Host "`n🔨 Building containers..." -ForegroundColor Yellow
    docker compose build
}

# Start services
Write-Host "`n🚀 Starting Tower services..." -ForegroundColor Yellow

$composeArgs = @("compose", "up")
if ($Detach) { $composeArgs += "-d" }

& docker @composeArgs

if ($Detach) {
    Write-Host "`n✅ Services gestartet!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Endpoints:" -ForegroundColor Cyan
    Write-Host "   Backend:    http://localhost:8000" -ForegroundColor White
    Write-Host "   Core:       http://localhost:8001" -ForegroundColor White
    Write-Host "   LLM-Bridge: http://localhost:3000" -ForegroundColor White
    Write-Host "   WebRelay:   http://localhost:3000" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Logs anzeigen:  docker compose logs -f" -ForegroundColor DarkGray
    Write-Host "💡 Stoppen:        .\stop_tower.ps1" -ForegroundColor DarkGray
}
