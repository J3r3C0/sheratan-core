<!-- README – Patch Append: Badges + Quality + Release -->
## Status & Badges
[![CI](https://github.com/J3r3C0/sheratan-core/actions/workflows/python-quality.yml/badge.svg)](https://github.com/J3r3C0/sheratan-core/actions/workflows/python-quality.yml)
[![OpenAPI Lint](https://github.com/J3r3C0/sheratan-core/actions/workflows/openapi-lint.yml/badge.svg)](https://github.com/J3r3C0/sheratan-core/actions/workflows/openapi-lint.yml)

## Release – HowTo
1. Merge in `main`
2. Tag setzen → Workflow veröffentlicht das Paket auf PyPI
   ```bash
   git tag core-vX.Y.Z
   git push origin core-vX.Y.Z
   ```
3. Changelog aktualisieren (Keep a Changelog / SemVer)

## Pre-commit Hooks
Installieren & aktivieren:
```bash
pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
```
Hooks: ruff (lint+format), mypy, basics (EoF, whitespace, merge-conflict).
