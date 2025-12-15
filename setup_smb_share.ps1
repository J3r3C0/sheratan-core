#== == == == == == == == == == == == == == == == == == == == == == =
#SHERATAN - SMB SHARE SETUP(Tower)
#Richtet Netzwerkfreigabe für Laptop - Zugriff ein
#MUSS ALS ADMINISTRATOR AUSGEFÜHRT WERDEN !
#== == == == == == == == == == == == == == == == == == == == == == =

#Requires - RunAsAdministrator

$ErrorActionPreference = "Stop"

                         Write -
                         Host "╔════════════════════════════════════════╗" -
                         ForegroundColor Green Write -
                         Host "║   SHERATAN SMB SHARE SETUP             ║" -
                         ForegroundColor Green Write -
                         Host "╚════════════════════════════════════════╝" -
                         ForegroundColor Green Write -
                         Host ""

                         $ShareName = "Sheratan" $SharePath = "C:\Sheratan"

#Check if running as admin
    $isAdmin =
        ([Security.Principal.WindowsPrincipal]
             [Security.Principal.WindowsIdentity] ::GetCurrent())
            .IsInRole([Security.Principal.WindowsBuiltInRole] ::
                          Administrator) if (-not $isAdmin){
                Write - Host "❌ Bitte als Administrator ausführen!" -
                ForegroundColor Red Write -
                Host "   Rechtsklick → 'Als Administrator ausführen'" -
                ForegroundColor Yellow exit 1}

#Check if share already exists
        $existingShare = Get - SmbShare - Name $ShareName -
                         ErrorAction SilentlyContinue if ($existingShare) {
  Write - Host "⚠️  Share '$ShareName' existiert bereits." -
      ForegroundColor Yellow Write - Host "   Pfad: $($existingShare.Path)" -
      ForegroundColor White

          $response = Read -
                      Host "   Neu erstellen? (j/n)" if ($response - ne "j"){
                          Write - Host "   Beende ohne Änderung." -
                          ForegroundColor Gray exit 0} Remove -
                      SmbShare - Name $ShareName - Force Write -
                      Host "   Alte Freigabe entfernt." - ForegroundColor Gray
}

#Create share
Write - Host "📁 Erstelle Netzwerkfreigabe..." - ForegroundColor Yellow New -
        SmbShare - Name $ShareName - Path $SharePath - FullAccess "Everyone" |
    Out -
        Null

#Allow through firewall
            Write -
        Host "🔥 Konfiguriere Firewall..." - ForegroundColor Yellow Enable -
        NetFirewallRule - DisplayGroup "File and Printer Sharing" -
        ErrorAction SilentlyContinue

            Write -
        Host "" Write - Host "✅ SMB Share eingerichtet!" -
        ForegroundColor Green Write - Host "" Write -
        Host "📍 Zugriff vom Laptop:" -
        ForegroundColor Cyan

#Get Tower IP
            $ip = (Get - NetIPAddress - AddressFamily IPv4 |
                   Where - Object{$_.InterfaceAlias - notmatch "Loopback" -
                                  and $_.IPAddress - notmatch "^169\."} |
                   Select - Object - First 1)
                      .IPAddress if ($ip) {
  Write - Host "   \\$ip\$ShareName" - ForegroundColor White Write -
      Host "" Write - Host "   Netzlaufwerk verbinden (auf Laptop):" -
      ForegroundColor Cyan Write -
      Host "   net use S: \\$ip\$ShareName /persistent:yes" -
      ForegroundColor Yellow
}
else {Write - Host "   \\<TOWER_IP>\$ShareName" - ForegroundColor White Write -
      Host "" Write - Host "   Ersetze <TOWER_IP> mit der IP dieses Rechners." -
      ForegroundColor Gray} Write -
    Host ""
