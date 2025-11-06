# Sheratan Core (sheratan-core)

Minimaler Orchestrator-Kern: Health, Version, LLM-Complete-Endpunkt (via dynamischen Router), Relay-Callback-Skelette,
JSON-Schemas und OpenAPI-Grundgerüst. Core hängt **nicht** von konkreten Routern ab.

## Quickstart
```bash
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn sheratan_core.api:app --host 0.0.0.0 --port 6060
```

## Router-Ladung
Der Core lädt einen Router dynamisch per ENV `SHERATAN_ROUTER` im Format `module:factory`.
Beispiel:
```
set SHERATAN_ROUTER=sheratan_router_openai.adapter:create_router
```

## Endpunkte
- `GET /health` → `{status:"ok"}`
- `GET /version` → metadaten
- `POST /api/v1/llm/complete` → `{"model","prompt","max_tokens"}` → routed an LLM-Router
- `POST /relay/status` / `POST /relay/final` → Callback-Skelette

## Schemas
Siehe `schemas/`. JSON-Schema ist die Quelle der Wahrheit; OpenAPI referenziert diese.
