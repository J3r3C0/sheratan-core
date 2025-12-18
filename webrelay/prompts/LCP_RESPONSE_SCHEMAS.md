# LCP Response Schemas - Complete Reference

## Overview
This document defines ALL valid LCP response formats for the Sheratan autonomous agent system.
ChatGPT must respond with EXACTLY one of these schemas - nothing else.

---

## 1. CREATE FOLLOW-UP JOBS (Continue Loop)

**When:** Agent needs more information or wants to delegate subtasks.

```json
{
  "ok": true,
  "action": "create_followup_jobs",
  "commentary": "Brief explanation of the plan",
  "new_jobs": [
    {
      "name": "List Python files",
      "kind": "list_files",
      "params": {
        "root": "C:\\Sheratan\\2_sheratan_core",
        "patterns": ["**/*.py"]
      },
      "auto_dispatch": true
    },
    {
      "name": "Read configuration",
      "kind": "read_file",
      "params": {
        "root": "C:\\Sheratan\\2_sheratan_core",
        "rel_path": "config.json"
      },
      "auto_dispatch": false
    }
  ]
}
```

**Available Job Kinds:**
- `list_files` - Enumerate files matching patterns
- `read_file` - Read file content
- `write_file` - Create or update a file
- `rewrite_file` - Overwrite entire file
- `agent_plan` - Create new planning job
- Any custom kind (system auto-creates task)

---

## 2. LIST FILES RESULT (Worker Response)

**When:** Worker completed a `list_files` job.

```json
{
  "ok": true,
  "action": "list_files_result",
  "files": [
    "core/main.py",
    "core/models.py",
    "worker/worker_loop.py"
  ],
  "root": "C:\\Sheratan\\2_sheratan_core",
  "patterns": ["**/*.py"]
}
```

---

## 3. READ FILE RESULT (Worker Response)

**When:** Worker completed a `read_file` job.

```json
{
  "ok": true,
  "action": "read_file_result",
  "path": "C:\\Sheratan\\2_sheratan_core\\main.py",
  "content": "import sys\nfrom core import start\n\nif __name__ == '__main__':\n    start()",
  "encoding": "utf-8",
  "size_bytes": 145
}
```

---

## 4. WRITE FILE (Agent Action)

**When:** Agent wants to create/modify a file.

```json
{
  "ok": true,
  "action": "write_file",
  "root": "C:\\Sheratan\\2_sheratan_core",
  "rel_path": "docs/ANALYSIS.md",
  "content": "# Analysis Results\n\n## Overview\nProject structure analyzed...",
  "mode": "overwrite"
}
```

**Modes:**
- `"overwrite"` - Replace entire file
- `"append"` - Add to end of file

---

## 5. ANALYSIS RESULT (End Loop - Success)

**When:** Agent completed analysis and has final recommendations.

```json
{
  "ok": true,
  "action": "analysis_result",
  "target_file": "core/main.py",
  "summary": "The main entry point initializes the core system and starts the event loop. It follows standard Python conventions.",
  "issues": [
    "Missing error handling in main()",
    "No logging configuration"
  ],
  "recommendations": [
    "Add try-except block around start()",
    "Initialize logger before calling start()"
  ]
}
```

---

## 6. MISSION COMPLETE (End Loop - Success)

**When:** Agent finished the entire mission successfully.

```json
{
  "ok": true,
  "action": "mission_complete",
  "summary": "Successfully analyzed Sheratan Core project. Created detailed documentation in ANALYSIS.md with 3 recommended refactorings.",
  "deliverables": [
    "ANALYSIS.md - Complete project analysis",
    "REFACTOR_PLAN.md - Step-by-step refactoring guide"
  ],
  "metrics": {
    "files_analyzed": 47,
    "issues_found": 12,
    "execution_time_seconds": 145
  }
}
```

---

## 7. ERROR RESPONSE (End Loop - Failure)

**When:** Agent encountered unrecoverable error.

```json
{
  "ok": false,
  "action": "error",
  "error": "Cannot access project root: directory does not exist",
  "error_code": "PATH_NOT_FOUND",
  "attempted_action": "list_files",
  "recovery_suggestion": "Verify project root path and retry mission"
}
```

---

## Job Kind Parameter Reference

### list_files
```json
"params": {
  "root": "C:\\path\\to\\project",
  "patterns": ["**/*.py", "*.md", "!**/node_modules/**"]
}
```

### read_file
```json
"params": {
  "root": "C:\\path\\to\\project",
  "rel_path": "src/main.py"
}
```
OR:
```json
"params": {
  "path": "C:\\path\\to\\project\\src\\main.py"
}
```

### write_file / rewrite_file
```json
"params": {
  "root": "C:\\path\\to\\project",
  "rel_path": "docs/OUTPUT.md",
  "new_content": "File content here..."
}
```

### agent_plan
```json
"params": {
  "user_prompt": "Analyze the database schema",
  "project_root": "C:\\path\\to\\project",
  "context": "Previous analysis found 3 tables..."
}
```

---

## Loop Termination Rules

**Loop CONTINUES when:**
- Response has `action: "create_followup_jobs"`
- Response creates at least 1 job with `auto_dispatch: true`

**Loop ENDS when:**
- Response has `action: "mission_complete"`
- Response has `action: "analysis_result"` 
- Response has `ok: false` (error)
- Response has `create_followup_jobs` but `new_jobs` is empty
- All jobs have `auto_dispatch: false` (waiting for user)

---

## Critical Rules

1. **Always respond with valid JSON only** - no explanatory text
2. **Pick exactly ONE action type** - never mix actions
3. **Use `mission_complete` when done** - prevents infinite loops
4. **Limit follow-up jobs to 3-5 max** - prevents queue explosion
5. **Set `auto_dispatch: false`** for jobs needing user review

---

## Example Mission Flow

```
1. agent_plan → create_followup_jobs (2 jobs: list_files, read_file)
   Queue: [list_files, read_file]

2. list_files → list_files_result → create_followup_jobs (read 3 files)
   Queue: [read_file, read_file, read_file, read_file]

3. read_file → read_file_result → create_followup_jobs (analyze)
   Queue: [read_file, read_file, read_file, agent_plan]

4. agent_plan → analysis_result (DONE!)
   Queue: [read_file, read_file, read_file]

5. Remaining jobs complete independently
```
