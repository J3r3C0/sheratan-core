# Sheratan Core POC

This repository contains the Proof of Concept (POC) for **Sheratan Core v2**, an autonomous agent system designed to execute missions using a Language Control Protocol (LCP).

## Architecture Overview

The system is composed of several Docker services that collaborate to execute tasks:

- **Core (`core/`)**: The central brain. It's a FastAPI application that manages:
  - **Missions**: High-level goals (e.g., "Refactor the database module").
  - **Tasks**: Steps within a mission.
  - **Jobs**: Concrete units of work (e.g., "Read file X", "Ask LLM Y").
  - **Dispatch**: Sends jobs to the worker via a file-based queue (`webrelay_out`).
  - **LCP Interpreter**: Parses results from the worker to automatically create follow-up jobs (Autonomous Loop).

- **Worker (`worker/`)**: A Python-based worker that:
  - Watches the `webrelay_out` directory for new job files.
  - Executes tools: `list_files`, `read_file`, `rewrite_file`.
  - Performs LLM calls (`llm_call`) using the configured provider (OpenAI, Ollama, etc.).
  - Writes results to `webrelay_in`.

- **WebRelay (`webrelay/`)**: A Node.js service for browser-based automation (optional/context-dependent).

- **Backend (`backend/`)**: Auxiliary service, likely for metrics and dashboard data.

- **Frontend (`frontend/`)**: A Vue/Vite-based UI for monitoring the system "HUD".

## Key Concepts

### LCP (Language Control Protocol)
The system relies on strict JSON communication with the LLM. The LLM is instructed to return actions in a specific format, such as:
```json
{
  "ok": true,
  "action": "create_followup_jobs",
  "new_jobs": [
    { "task": "read_file", "params": { "path": "main.py" } }
  ]
}
```
The **Core** interprets this response and automatically creates the `read_file` job, enabling the agent to "think" and "act" autonomously.

### File-Based Queue
Communication between Core and Worker happens via shared Docker volumes:
- **`relay-out`**: Core writes `.job.json` files here.
- **`relay-in`**: Worker writes `.result.json` files here.
This decouples the system and allows for different worker implementations (Python, Node.js, etc.).

## Getting Started

### Quick Start: Tower vs Laptop Mode

This package supports two deployment modes:

| Mode | Description | Script |
|------|-------------|--------|
| **Tower** | Full Docker stack (all services) | `.\start_tower.ps1` |
| **Laptop** | Thin client connecting to Tower | `.\start_laptop.ps1` |

---

### Tower Setup (Desktop/Standrechner)

1. **Configure Environment**:
   ```powershell
   cp .env.example .env
   # Edit .env with your LLM settings
   ```

2. **Start All Services**:
   ```powershell
   .\start_tower.ps1 -Build -Detach
   ```

3. **Enable SMB Share** (for Laptop development access):
   ```powershell
   # Run as Administrator!
   .\setup_smb_share.ps1
   ```

---

### Laptop Setup (Remote Development)

1. **Connect to Tower Share**:
   ```powershell
   net use S: \\<TOWER_IP>\Sheratan /persistent:yes
   ```

2. **Set Tower Host**:
   ```powershell
   setx SHERATAN_TOWER_HOST "<TOWER_IP>"
   ```

3. **Start Laptop Mode**:
   ```powershell
   .\start_laptop.ps1
   ```

---

### Services & Ports

| Service | Port | Description |
|---------|------|-------------|
| Backend | 8000 | API Gateway |
| Core | 8001 | Mission Engine |
| LLM-Bridge | 3000 | LLM Proxy |
| WebRelay | 3000 | Browser Automation |

4. **Usage**:
   - Access the Core API at `http://localhost:8001`.
   - Create a Mission via the API or Dashboard.
   - The system will dispatch jobs and the Worker will process them.

## Directory Structure
- `core/`: FastAPI application code.
  - `sheratan_core_v2/lcp_actions.py`: Logic for interpreting LLM responses.
  - `sheratan_core_v2/main.py`: Main API endpoints.
- `worker/`: Worker implementation.
  - `worker_loop.py`: Main loop for processing jobs.
- `project/`: The workspace directory where the agent operates (mounted to `/workspace/project` in the worker).

