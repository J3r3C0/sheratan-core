"""
Cleanup-Script: Löscht Missions die nur 1 Job haben (Clone-Missions)
"""
import requests

BASE_URL = "http://localhost:8001/api"

def get_missions():
    return requests.get(f"{BASE_URL}/missions").json()

def get_tasks():
    return requests.get(f"{BASE_URL}/tasks").json()

def get_jobs():
    return requests.get(f"{BASE_URL}/jobs").json()

def count_jobs_for_mission(mission_id, tasks, jobs):
    """Zählt Jobs einer Mission über Tasks"""
    mission_tasks = [t for t in tasks if t.get('mission_id') == mission_id]
    task_ids = {t['id'] for t in mission_tasks}
    mission_jobs = [j for j in jobs if j.get('task_id') in task_ids]
    return len(mission_jobs)

def delete_mission(mission_id):
    """Löscht eine Mission"""
    resp = requests.delete(f"{BASE_URL}/missions/{mission_id}")
    return resp.status_code

def main():
    print("=== SHERATAN CLEANUP: Clone-Missions löschen ===\n")
    
    missions = get_missions()
    tasks = get_tasks()
    jobs = get_jobs()
    
    print(f"Gefunden: {len(missions)} Missions, {len(tasks)} Tasks, {len(jobs)} Jobs\n")
    
    # Finde Missions mit nur 1 Job
    to_delete = []
    to_keep = []
    
    for m in missions:
        job_count = count_jobs_for_mission(m['id'], tasks, jobs)
        info = f"{m['id'][:8]}... | Jobs: {job_count:3d} | {m.get('name', 'no-name')}"
        
        if job_count <= 1:
            to_delete.append((m['id'], info))
        else:
            to_keep.append((m['id'], info))
    
    print("--- BEHALTE (>1 Job) ---")
    for _, info in to_keep:
        print(f"  ✓ {info}")
    
    print(f"\n--- ZU LÖSCHEN (<=1 Job): {len(to_delete)} ---")
    for _, info in to_delete:
        print(f"  ✗ {info}")
    
    if not to_delete:
        print("\nKeine Clone-Missions gefunden. Nichts zu löschen.")
        return
    
    # Bestätigung
    print(f"\n⚠️  {len(to_delete)} Mission(s) werden gelöscht!")
    confirm = input("Fortfahren? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Abgebrochen.")
        return
    
    # Löschen
    print("\nLösche...")
    deleted = 0
    for mission_id, info in to_delete:
        status = delete_mission(mission_id)
        if status in [200, 204]:
            print(f"  ✓ Gelöscht: {mission_id[:8]}...")
            deleted += 1
        else:
            print(f"  ✗ Fehler ({status}): {mission_id[:8]}...")
    
    print(f"\n=== Fertig: {deleted}/{len(to_delete)} gelöscht ===")

if __name__ == "__main__":
    main()
