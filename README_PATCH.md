# sheratan-core — Quality Patch
Branch: `chore/quality-openapi-mypy-ruff`

## Apply
```bash
git checkout -b chore/quality-openapi-mypy-ruff
# Kopiere die Dateien ins Repo-Root (behalte Struktur bei)
git add -A
git commit -m "chore(core): OpenAPI lint + ruff + mypy + dev-requirements"
git push -u origin chore/quality-openapi-mypy-ruff
gh pr create --title "chore(core): OpenAPI lint + ruff + mypy" --body "Adds Redocly OpenAPI lint, ruff config, mypy config & CI workflows"
```
