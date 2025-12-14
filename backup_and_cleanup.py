"""
Sheratan Data Backup & Cleanup Script
Creates backup of all missions, tasks, jobs then deletes them.
"""
import requests
import json
import os
from datetime import datetime

# API Base URL
BASE = "http://localhost:8001/api"

# Backup folder
BACKUP_DIR = f"backup_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"

def main():
    print("\n" + "="*50)
    print("  SHERATAN BACKUP & CLEANUP")
    print("="*50 + "\n")
    
    # Create backup folder
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print(f"[BACKUP] Ordner: {BACKUP_DIR}\n")
    
    # 1. Fetch & Save Missions
    print("[1/6] Lade Missions...")
    try:
        missions = requests.get(f"{BASE}/missions").json()
        with open(f"{BACKUP_DIR}/missions.jsonl", "w", encoding="utf-8") as f:
            for m in missions:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        print(f"      OK: {len(missions)} Missions gesichert")
    except Exception as e:
        print(f"      FEHLER: {e}")
        missions = []
    
    # 2. Fetch & Save Tasks
    print("[2/6] Lade Tasks...")
    try:
        tasks = requests.get(f"{BASE}/tasks").json()
        with open(f"{BACKUP_DIR}/tasks.jsonl", "w", encoding="utf-8") as f:
            for t in tasks:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        print(f"      OK: {len(tasks)} Tasks gesichert")
    except Exception as e:
        print(f"      FEHLER: {e}")
        tasks = []
    
    # 3. Fetch & Save Jobs
    print("[3/6] Lade Jobs...")
    try:
        jobs = requests.get(f"{BASE}/jobs").json()
        with open(f"{BACKUP_DIR}/jobs.jsonl", "w", encoding="utf-8") as f:
            for j in jobs:
                f.write(json.dumps(j, ensure_ascii=False) + "\n")
        print(f"      OK: {len(jobs)} Jobs gesichert")
    except Exception as e:
        print(f"      FEHLER: {e}")
        jobs = []
    
    print(f"\n[BACKUP] Abgeschlossen in: {BACKUP_DIR}/")
    print(f"   - missions.jsonl ({len(missions)} Eintraege)")
    print(f"   - tasks.jsonl ({len(tasks)} Eintraege)")
    print(f"   - jobs.jsonl ({len(jobs)} Eintraege)")
    
    # 4. Delete Jobs
    print("\n[4/6] Loesche Jobs...")
    deleted_jobs = 0
    for job in jobs:
        try:
            r = requests.delete(f"{BASE}/jobs/{job['id']}")
            if r.status_code < 300:
                deleted_jobs += 1
        except:
            pass
    print(f"      OK: {deleted_jobs} Jobs geloescht")
    
    # 5. Delete Tasks
    print("[5/6] Loesche Tasks...")
    deleted_tasks = 0
    for task in tasks:
        try:
            r = requests.delete(f"{BASE}/tasks/{task['id']}")
            if r.status_code < 300:
                deleted_tasks += 1
        except:
            pass
    print(f"      OK: {deleted_tasks} Tasks geloescht")
    
    # 6. Delete Missions
    print("[6/6] Loesche Missions...")
    deleted_missions = 0
    for mission in missions:
        try:
            r = requests.delete(f"{BASE}/missions/{mission['id']}")
            if r.status_code < 300:
                deleted_missions += 1
        except:
            pass
    print(f"      OK: {deleted_missions} Missions geloescht")
    
    print("\n" + "="*50)
    print("  FERTIG!")
    print("="*50)
    print(f"\n[OK] Backup: {BACKUP_DIR}/")
    print(f"[OK] Geloescht: {deleted_missions} Missions, {deleted_tasks} Tasks, {deleted_jobs} Jobs")
    print("\nSystem ist bereit fuer einen sauberen Start!\n")

if __name__ == "__main__":
    main()
