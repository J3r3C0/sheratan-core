"""memory/schema.py
Kompakte Schema-Definitionen / Kommentare (Deutsch).
"""
# EventRecord:
# eid: hex string (sha256, 64 chars)
# ts: unix ms (int64)
# etype: small int
# meta: kompaktes json (z.B. {'src':'radio0','len':32})
# pref: chunk-hash oder None
# score: float
