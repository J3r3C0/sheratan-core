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

## Quality Status

[![CI](https://github.com/J3r3C0/sheratan-core/actions/workflows/ci.yml/badge.svg)](https://github.com/J3r3C0/sheratan-core/actions/workflows/ci.yml)
[![OpenAPI Docs](https://img.shields.io/badge/OpenAPI-Docs-00A3D9)](https://J3r3C0.github.io/sheratan-core)
[![PyPI](https://img.shields.io/pypi/v/sheratan-core.svg)](https://pypi.org/project/sheratan-core/)
[![Release Please](https://img.shields.io/badge/Release--Please-enabled-success)](https://github.com/googleapis/release-please)

### Release How-To
1. Conventional Commit mergen (feat/fix/chore/docs�).
2. **release-please** �ffnet Auto-PR ? mergen.
3. Tag core-vX.Y.Z wird erstellt ? PyPI-Publish l�uft.
4. Release-Notes enthalten OpenAPI-Link & SHA256 der Wheels.


## OpenAPI Docs

[![OpenAPI](https://img.shields.io/badge/OpenAPI-Docs-00A3D9?logo=openapiinitiative&logoColor=white)](https://j3r3c0.github.io/sheratan-core)

This project publishes its API reference automatically via **GitHub Pages**.
Each new release updates the [Redoc](https://github.com/Redocly/redoc) preview
from the latest \openapi.yaml\ in the main branch.

- **Docs URL:** [https://j3r3c0.github.io/sheratan-core](https://j3r3c0.github.io/sheratan-core)
- **Spec file:** [openapi.yaml](./openapi.yaml)
- **Renderer:** Redoc (CDN build, no paywall)
- **Deployment Guide:** See [GITHUB_PAGES_DEPLOYMENT.md](./GITHUB_PAGES_DEPLOYMENT.md) for instructions on triggering the deployment

