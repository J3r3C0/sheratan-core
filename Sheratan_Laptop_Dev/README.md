# Sheratan Laptop Dev (no Docker)
This bundle is meant to run on the **laptop** while the heavy Docker stack runs on your **tower** on the same hotspot/LAN.

## What runs where
**Tower (Docker):**
- WebRelay / LLM bridge (HTTP)  -> `http://<TOWER_HOST>:3000`
- Optional core backend / api    -> `http://<TOWER_HOST>:8000` (if you have it)
- Anything heavy (DB, workers, GPU etc.)

**Laptop (this ZIP):**
- Sheratan Core dev loop (Python)
- Streamlit dashboard
- Thin client that calls the tower endpoints

## Quick start (Windows PowerShell)
1) Unzip to e.g. `C:\Sheratan_Laptop_Dev`
2) Create venv + install:
```powershell
cd C:\Sheratan_Laptop_Dev
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

3) Set your tower IP/host (choose ONE):
```powershell
setx SHERATAN_TOWER_HOST "192.168.0.2"  /setx SHERATAN_TOWER_HOST "TOWER"
# or hostname, e.g. "TOWER"
```

4) Start everything (3 terminals is fine, or use the provided launcher):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_local.ps1
```

## Ports (default)
- Laptop UI:        http://localhost:8501
- Tower WebRelay:   http://%SHERATAN_TOWER_HOST%:3000
- Tower Backend:    http://%SHERATAN_TOWER_HOST%:8000  (optional)

## Config
- `configs/laptop_dev.env` contains defaults.
- Any env var overrides config.

## Notes
- This is intentionally minimal and laptop-friendly: no WSL, no Docker.
- If you later want a single "start all" on laptop, add a supervisor (optional).




# dev_docker_auf_tower_server

Tower fährt den Docker-Stack (LLM-Proxy + Sheratan-Core-Service) im selben Hotspot/LAN.
Laptop nutzt dazu passend `laptop_dev.zip` und spricht den Tower per IP/Ports an.

## Default Services
- llm-bridge (Node/Express) :3000 → Proxy/Forwarder für LLM-Calls
- sheratan-core (FastAPI) :8000 → Minimaler Core-Service (health + LLM ping)

## Quickstart
```bash
cd docker
cp .env.example .env   # falls noch nicht vorhanden
docker compose up -d --build
docker compose logs -f
```

## Health
- http://<TOWER_IP>:3000/health
- http://<TOWER_IP>:8000/health

## Laptop Matching
Laptop zeigt auf:
- SHERATAN_WEBRELAY_URL=http://<TOWER_IP>:3000/api/llm/call
