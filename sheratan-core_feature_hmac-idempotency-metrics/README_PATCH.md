# sheratan-core — Patch PR
Branch: `feature/hmac-idempotency-metrics`

## Apply
```bash
# from repo root (sheratan-core)
git checkout -b feature/hmac-idempotency-metrics
# copy these files/folders over the repo
# (or unzip into repo root, then:)
git add -A
git commit -m "feat(core): HMAC verify, idempotency (mem+sqlite), metrics endpoint, request timing"
git push -u origin feature/hmac-idempotency-metrics
gh pr create --title "feat(core): HMAC + idempotency + metrics" --body "Adds HMAC verify for relay callbacks, idempotency store (mem+sqlite), request timing and /metrics endpoint"
```
