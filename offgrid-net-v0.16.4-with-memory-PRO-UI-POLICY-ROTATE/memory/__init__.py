# memory package for Offgrid-Net v0.17.0
# Deutsch kommentiert: Kernfunktionen zur Speicherung, Kompaktierung und Budgetverwaltung
from .store import MemoryStore
from .synopses import Bloom, Reservoir
from .retention import allocate_budget, compute_effective_budget
from .compact import compact_window
