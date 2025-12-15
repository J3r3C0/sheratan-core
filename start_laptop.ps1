#== == == == == == == == == == == == == == == == == == == == == == =
#SHERATAN CORE - LAPTOP MODE
#Verbindet sich zu Tower für LLM - Calls
#== == == == == == == == == == == == == == == == == == == == == == =

param([string] $TowerHost = $env : SHERATAN_TOWER_HOST)

    $ErrorActionPreference =
        "Stop"

        Write
        - Host "╔════════════════════════════════════════╗" -
        ForegroundColor Magenta Write
        - Host "║   SHERATAN CORE - LAPTOP MODE          ║" -
        ForegroundColor Magenta Write
        - Host "╚════════════════════════════════════════╝" -
        ForegroundColor Magenta Write -
        Host ""

#Get script directory
        $ScriptDir =
            Split - Path - Parent $MyInvocation.MyCommand.Path Set -
            Location $ScriptDir

#Check Tower Host
            if (-not $TowerHost){
                Write - Host "❌ SHERATAN_TOWER_HOST nicht gesetzt!" -
                ForegroundColor Red Write - Host "" Write - Host "Optionen:" -
                ForegroundColor Yellow Write -
                Host
                "  1. Parameter: .\start_laptop.ps1 -TowerHost 192.168.x.x" -
                ForegroundColor White Write -
                Host
                "  2. Env-Var:   `$env:SHERATAN_TOWER_HOST = '192.168.x.x'" -
                ForegroundColor White Write -
                Host "  3. System:    setx SHERATAN_TOWER_HOST '192.168.x.x'" -
                ForegroundColor White exit 1}

            Write
            - Host "🔗 Tower Host: $TowerHost" -
            ForegroundColor Cyan

#Check Tower reachability
            Write
            - Host "🔍 Prüfe Tower-Verbindung..." - ForegroundColor Yellow try {
  $health = Invoke - RestMethod "http://${TowerHost}:8000/health" -
            TimeoutSec 5 Write - Host "✓ Tower Backend erreichbar" -
            ForegroundColor Green
} catch {
  Write - Host "⚠️  Tower Backend nicht erreichbar auf :8000" -
      ForegroundColor Yellow
}

try {
  $health = Invoke - RestMethod "http://${TowerHost}:3000/health" -
            TimeoutSec 5 Write - Host "✓ Tower LLM-Bridge erreichbar" -
            ForegroundColor Green
} catch {
  Write - Host "⚠️  Tower LLM-Bridge nicht erreichbar auf :3000" -
      ForegroundColor Yellow
}

#Set environment for Tower communication
$env : SHERATAN_WEBRELAY_URL = "http://${TowerHost}:3000/api/llm/call" $env
    : SHERATAN_TOWER_BACKEND_URL =
          "http://${TowerHost}:8000"

          Write -
          Host "" Write - Host "📍 Tower Endpoints konfiguriert:" -
          ForegroundColor Cyan Write -
          Host "   SHERATAN_WEBRELAY_URL:       $env:SHERATAN_WEBRELAY_URL" -
          ForegroundColor White Write -
          Host
          "   SHERATAN_TOWER_BACKEND_URL:  $env:SHERATAN_TOWER_BACKEND_URL" -
          ForegroundColor White Write -
          Host ""

#Start dashboard
          if (Test - Path "react-dashboard"){
              Write - Host "🚀 Starte React Dashboard..." -
              ForegroundColor Yellow Set -
              Location
              "react-dashboard" npm run dev} elseif(Test - Path "index.html"){
              Write - Host "🌐 Öffne Dashboard im Browser..." -
              ForegroundColor Yellow Start - Process "index.html"} else {
  Write - Host "✅ Laptop Mode aktiv. Tower-Endpoints sind gesetzt." -
      ForegroundColor Green Write - Host "" Write -
      Host "💡 Du kannst jetzt deine lokalen Tools nutzen." -
      ForegroundColor DarkGray
}
