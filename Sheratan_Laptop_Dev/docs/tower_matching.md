# Matching the tower Docker ZIP
This laptop bundle assumes the tower exposes:

- WebRelay/LLM bridge: `:3000/api/llm/call`
- (Optional) backend API: `:8000`

If your tower ZIP uses different ports/paths, just set:
- `SHERATAN_WEBRELAY_URL`
- `SHERATAN_TOWER_BACKEND_URL`

Example:
```powershell
setx SHERATAN_TOWER_HOST "192.168.137.1"
setx SHERATAN_WEBRELAY_URL "http://%SHERATAN_TOWER_HOST%:3000/api/llm/call"


# Tower ↔ Laptop Matching

Laptop → Tower:
- SHERATAN_WEBRELAY_URL=http://<TOWER_IP>:3000/api/llm/call

Tower Bridge → Upstream:
- SHERATAN_UPSTREAM_LLM_URL=...

Optional Token:
- Wenn LLM_BRIDGE_TOKEN gesetzt ist, muss der Laptop `x-sheratan-token` mitsenden.
```
