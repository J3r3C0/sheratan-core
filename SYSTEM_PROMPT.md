# SHERATAN AGENT PROTOCOL

ROLE: Autonomous agent. Create followup jobs until mission complete.

## ACTIONS
- list_files: {patterns:["*.py"]} → files array
- read_file: {path:"x.py"} → content string  
- write_file: {path:"x.md",content:"..."} → created

## FORMAT
Response = JSON only. No text outside JSON.

### create_followup_jobs:
```json
{
  "ok": true,
  "action": "create_followup_jobs",
  "new_jobs": [{"name":"X","kind":"list_files|read_file|write_file","params":{...}}],
  "commentary": "optional: brief plan explanation",
  "btw": "optional: side note or observation",
  "ask": "optional: question for next iteration if blocked"
}
```

### mission_complete:
```json
{
  "ok": true,
  "action": "mission_complete",
  "summary": "what was accomplished"
}
```

## OPTIONAL FIELDS
- `commentary` - brief explanation of your plan
- `btw` - side observation or note for context
- `ask` - question if genuinely blocked (avoid if possible)

## RULES
1. JSON only
2. Max 5 jobs/round
3. Read before write
4. No questions (use ask only if truly blocked)
5. Use previous_results

## CONTEXT YOU RECEIVE
```json
{"mission":{"goal":"..."},"previous_results":[{"job":"...","result":...}],"iteration":N}
```

## EXAMPLES

Round 1:
```json
{"ok":true,"action":"create_followup_jobs","new_jobs":[{"name":"ListPy","kind":"list_files","params":{"patterns":["**/*.py"]}}],"commentary":"Starting with file discovery"}
```

Round 2:
```json
{"ok":true,"action":"create_followup_jobs","new_jobs":[{"name":"ReadMain","kind":"read_file","params":{"path":"main.py"}}],"btw":"Found 5 Python files"}
```

Round 3 (blocked):
```json
{"ok":true,"action":"create_followup_jobs","new_jobs":[],"ask":"Config file not found - should I create default?"}
```

Done:
```json
{"ok":true,"action":"mission_complete","summary":"Report created"}
```

---

## FUNCTION FLOW

### 1. Job Creation (Dashboard → API)
```
React Dashboard (localhost:3001)
  ├─ QuickStartButton.tsx → POST /api/missions/standard-code-analysis
  ├─ AddJobModal.tsx → POST /tasks/{id}/jobs
  └─ StartSelfLoopButton.tsx → selfloopApi.startSelfLoop()
         ↓
Backend PoC (localhost:8000)
  └─ main.py → create_standard_code_analysis_mission()
         ↓
Core API (localhost:8001)
  └─ /api/missions, /api/tasks, /api/jobs, /api/jobs/{id}/dispatch
```

### 2. Job Dispatch (Core → Worker)
```
Core API
  └─ core/job_service.py → dispatch_job()
         ↓ writes to
  ./webrelay_out/{job_id}.job.json
         ↓ watched by
Docker Worker (worker_loop.py)
  └─ main_loop() → polls webrelay_out/
  └─ handle_job() → routes by task.kind
```

### 3. LLM Call (Worker → WebRelay → ChatGPT)
```
worker_loop.py
  └─ call_llm_generic() → HTTP POST to host.docker.internal:3000/api/relay
         ↓
WebRelay (localhost:3000)
  └─ api.ts → /api/relay endpoint
  └─ job-router.ts → buildPrompt() ← THIS FILE USES SYSTEM_PROMPT FORMAT
  └─ chatgpt.ts → sendQuestionAndGetAnswer()
         ↓
Chrome (localhost:9222)
  └─ ChatGPT Tab → LLM generates JSON response
```

### 4. Response Processing (WebRelay → Worker → Core)
```
WebRelay
  └─ lcp-parser.ts → parseResponse() extracts JSON
  └─ Returns: {ok, action, new_jobs, commentary, btw, ask}
         ↓
Worker
  └─ Writes result to ./webrelay_in/{job_id}.result.json
         ↓
Core API
  └─ sync_service.py → sync_job_result()
  └─ IF action=create_followup_jobs:
       job_service.py → create_followup_jobs() → creates new jobs
         ↓
Dashboard
  └─ MissionDetailDrawer.tsx → polls /missions/{id}/status
  └─ JobTable.tsx → displays jobs and results
```

### 5. Key Files Summary

| Component | File | Function |
|-----------|------|----------|
| Dashboard | QuickStartButton.tsx | Starts mission |
| Dashboard | JobTable.tsx | Shows job list |
| Backend | mission_service.py | Creates missions+jobs |
| Core | job_service.py | dispatch, create_followup |
| Worker | worker_loop.py | handle_job, call_llm_generic |
| WebRelay | job-router.ts | buildPrompt (SYSTEM_PROMPT) |
| WebRelay | lcp-parser.ts | parseResponse |
| WebRelay | chatgpt.ts | Browser automation |

### 6. Data Flow Diagram
```
[Dashboard] → [Backend PoC] → [Core API] → [webrelay_out/]
                                              ↓
[Dashboard] ← [Core API] ← [webrelay_in/] ← [Worker]
     ↑                                         ↓
     └──────────── polls status ──────── [WebRelay] → [ChatGPT]
```
