# Sheratan Core – Tower/Laptop Setup Guide

Schritt-für-Schritt Anleitung zum Einrichten des Sheratan Core auf Tower und Laptop.

---

## 📋 Voraussetzungen

- **Tower**: Windows PC mit Docker Desktop
- **Laptop**: Windows PC im gleichen Netzwerk
- **Git**: Auf beiden Geräten installiert

---

## 🖥️ TEIL 1: Tower einrichten

### Schritt 1: Repository klonen
```powershell
cd C:\
git clone https://github.com/J3r3C0/sheratan-core.git Sheratan\2_sheratan_core
cd Sheratan\2_sheratan_core
```

### Schritt 2: Umgebung konfigurieren
```powershell
cp .env.example .env
notepad .env   # LLM-Einstellungen anpassen
```

### Schritt 3: SMB-Freigabe einrichten
> ⚠️ **Als Administrator ausführen!**

```powershell
.\setup_smb_share.ps1
```

Dieses Script:
- Gibt `C:\Sheratan` als Netzlaufwerk frei
- Zeigt dir die Tower-IP für den Laptop an

### Schritt 4: Docker-Stack starten
```powershell
.\start_tower.ps1 -Build -Detach
```

### Schritt 5: Prüfen ob alles läuft
```powershell
# Health-Checks
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:3000/health
```

---

## 💻 TEIL 2: Laptop einrichten

### Schritt 1: Tower-IP notieren
Die IP wurde beim SMB-Setup angezeigt, z.B. `192.168.1.100`

### Schritt 2: Netzlaufwerk verbinden
```powershell
net use S: \\192.168.1.100\Sheratan /persistent:yes
```

### Schritt 3: Tower-Host setzen
```powershell
setx SHERATAN_TOWER_HOST "192.168.1.100"
```

### Schritt 4: In VS Code / Antigravity öffnen
Öffne das Laufwerk `S:\2_sheratan_core` – Änderungen gehen direkt auf den Tower!

### Schritt 5: Laptop-Mode starten (optional)
```powershell
cd S:\2_sheratan_core
.\start_laptop.ps1
```

---

## 📁 Script-Übersicht

| Script | Beschreibung | Wo ausführen |
|--------|--------------|--------------|
| `start_tower.ps1` | Startet alle Docker-Services | Tower |
| `stop_tower.ps1` | Stoppt alle Container | Tower |
| `start_laptop.ps1` | Verbindet zu Tower-Services | Laptop |
| `setup_smb_share.ps1` | Richtet SMB-Freigabe ein | Tower (Admin) |

---

## 🔗 Endpoints

| Service | URL | Beschreibung |
|---------|-----|--------------|
| Backend | http://TOWER_IP:8000 | API Gateway |
| Core | http://TOWER_IP:8001 | Mission Engine |
| LLM-Bridge | http://TOWER_IP:3000 | LLM Proxy |

---

## ❓ Troubleshooting

### SMB-Verbindung schlägt fehl
```powershell
# Firewall prüfen
Get-NetFirewallRule -DisplayGroup "File and Printer Sharing" | Select Name, Enabled
```

### Docker startet nicht
```powershell
# Docker Desktop starten und prüfen
docker info
```

### Tower nicht erreichbar
```powershell
# Ping vom Laptop aus
ping 192.168.1.100
```
