# 🎛️ Sheratan Dashboard Guide

## Dashboards Overview

Sheratan now has **3 optimized dashboards** für verschiedene Use Cases:

### 1. 🚀 Minimal Control Panel (Schnellzugriff)
**Datei:** `core/sheratan_core_v2/sheratan-minimal-control.html`  
**URL:** [http://localhost:8001/sheratan-minimal-control.html](http://localhost:8001/sheratan-minimal-control.html)

**Features:**
- ⚡ Ultra-lightweight & schnell
- 2-Panel Layout (Prompt + Output)
- Core Status & WebRelay Status
- 2 Modi:
  - **Core Mission Flow** (Startet autonomen Loop)
  - **Direkter LLM Call** (Schnelle Frage ohne Loop)

**Perfekt für:** Schnelle Tests, einfaches LLM-Prompting

---

### 2. 📊 Full Dashboard (Komplett)
**Datei:** `sheratan-dashboard.html`  
**URL:** Direkt öffnen: `file:///c:/sheratan-core-poc/sheratan-dashboard.html`

**Features:**
- 🎨 4 Seiten: Overview, Missions, Jobs, Console
- Mission Management (erstellen, details ansehen)
- Job Queue mit Filter (pending/done/failed)
- Task Overview pro Mission
- Live Status Cards (Core, WebRelay, offene Jobs)
- Auto-Refresh alle 5s

**Perfekt für:** Überwachen des autonomen Loops, Mission-Management

---

### 3. ⚛️ React Dashboard (TypeScript)
**Datei:** `SheratanDashboard.tsx`  
**Framework:** React + TypeScript

**Features:**
- Identisch mit Full Dashboard
- React Components
- TypeScript Type Safety
- Optional Tailwind CSS

**Perfekt für:** Integration in React App, Development

**Setup:**
```tsx
import SheratanDashboard from "./SheratanDashboard";

<SheratanDashboard />
```

---

## API Endpoints

Alle Dashboards nutzen diese URLs:

```javascript
const CORE_BASE_URL = "http://localhost:8001";
const WEBRELAY_BASE_URL = "http://localhost:3000";
```

**Core API:** `http://localhost:8001/api/`
- `/api/status` - System Status
- `/api/missions` - Missions CRUD
- `/api/tasks` - Tasks CRUD
- `/api/jobs` - Jobs CRUD
- `/api/jobs/{id}/dispatch` - Job starten
- `/api/jobs/{id}/sync` - Job Result abrufen

**WebRelay API:** `http://localhost:3000/`
- `/health` - Health Check
- `/api/llm/call` - Direkter LLM Call

---

## Cleanup Done ✅

**Entfernt (RAM-Optimierung):**
- ❌ `frontend/` Ordner (komplettes React Vite Build - verschwendete Docker RAM)
- ❌ `index.html` (altes HUD)
- ❌ `control-dashboard.html` (durch sheratan-dashboard.html ersetzt)

**Behalten:**
- ✅ `sheratan-minimal-control.html` (minimal)
- ✅ `sheratan-dashboard.html` (full)
- ✅ `SheratanDashboard.tsx` (React)

---

## Quick Start

### Option 1: Minimal Panel (schnellster Zugriff)
1. **`start_core.bat`** doppelklicken (startet Docker)
2. **`start_webrelay.bat`** doppelklicken (startet WebRelay)
3. Browser: http://localhost:8001/sheratan-minimal-control.html

### Option 2: Full Dashboard
1. **`start_core.bat`** doppelklicken (startet Docker)
2. **`start_webrelay.bat`** doppelklicken (startet WebRelay)
3. Dashboard öffnen: `file:///c:/sheratan-core-poc/sheratan-dashboard.html`

### Option 3: React Dashboard ⚛️
**Ordner:** `react-dashboard/`  
**URL:** http://localhost:5173  
**Framework:** Vite + React + TypeScript

**Features:**
- Identisch mit Full Dashboard
- React Components mit TypeScript
- Tailwind CSS Styling
- Hot Module Reload
- Production Build möglich

**Setup:**
```bash
cd react-dashboard
npm install        # Einmalig: Dependencies installieren
npm run dev        # Dev Server starten
```

**Oder:** `start.bat` doppelklicken! 🎯

**Perfekt für:** Integration in größere React App, moderne Development

---

## Empfehlung

**Für tägliche Nutzung:**
- 🚀 Minimal Panel → Schnelle Tests & Prompts
- 📊 Full Dashboard → Monitoring & Mission Management

**Für Development:**
- ⚛️ React Dashboard → Integration in größere App

---

## Autonomous Loop Testen

**Im Minimal Panel:**
1. Prompt eingeben: `"Analyze all Python files and create a summary"`
2. **"Core Mission Flow"** Tab wählen
3. "Prompt ausführen" klicken
4. → Startet Mission → Task → Job → Autonomous Loop! 🔄

**Im Full Dashboard:**
1. Console Seite öffnen
2. Selber Prompt
3. **"Send to Loop"** (Core Flow Tab)
4. → ChatGPT Window beobachten - du siehst 20+ autonome Iterationen! 🚀

---

**Status:** ✅ Alle Dashboards ready & optimiert!
