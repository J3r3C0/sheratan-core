#== == == == == == == == == == == == == == == == == == == == == == =
#SHERATAN CORE - TOWER STOP
#Stoppt alle Docker - Services
#== == == == == == == == == == == == == == == == == == == == == == =

$ErrorActionPreference =
    "Stop"

    Write -
    Host "🛑 Stopping Tower services..." -
    ForegroundColor Yellow

        $ScriptDir = Split - Path - Parent $MyInvocation.MyCommand.Path Set -
                     Location $ScriptDir

                         docker compose down

                             Write -
                     Host "✅ Alle Services gestoppt." - ForegroundColor Green
