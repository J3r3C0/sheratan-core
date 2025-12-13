"""memory/retention.py
Budget-Policy und Hilfsfunktionen zur Berechnung effektiver Budgets.
Deutsch kommentiert.
"""
def allocate_budget(total_mb: int):
    """Zerteilt das Gesamtbudget in sinnvolle Teile (Events, Summaries, Chunks, Indices)."""
    B = total_mb * 1024 * 1024
    return {
        'events': int(B * 0.40),
        'summaries': int(B * 0.25),
        'chunks': int(B * 0.25),
        'indices': int(B * 0.10)
    }

def get_hardcap(base_mb: int):
    if base_mb <= 16:
        return 16
    elif base_mb <= 64:
        return 64
    elif base_mb <= 128:
        return 128
    elif base_mb <= 256:
        return 256
    else:
        return 512

def compute_effective_budget(base_mb: int, token_level: int=0):
    mult = {0:1.0, 1:1.25, 2:1.5, 3:2.0}.get(token_level, 1.0)
    eff = int(base_mb * mult)
    hard = get_hardcap(base_mb)
    return min(eff, hard)
