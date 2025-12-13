# Placeholder für Replikations-/EC-Logik. In v0 nur API-Skizze.

def replicate_chunks(chunks, r=5):
    # naive Kopien-Zähler (kein Netzwerkcode in v0)
    copies = []
    for c in chunks:
        copies.append({**c, "replicas": r})
    return copies
