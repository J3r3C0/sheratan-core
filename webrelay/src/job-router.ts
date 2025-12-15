// ========================================
// Sheratan WebRelay - Job Router & Prompt Builder
// ========================================

import { UnifiedJob } from './types.js';

/**
 * Build prompt from UnifiedJob
 * Extracts relevant parts based on job.kind and payload structure
 */
export class JobRouter {
  buildPrompt(job: UnifiedJob): string {
    const { payload } = job;

    // Direct prompt field (simple llm_call)
    if (payload.prompt) {
      return payload.prompt;
    }

    // agent_plan format: task.params.user_prompt
    if (job.kind === 'agent_plan' && payload.task?.params?.user_prompt) {
      const userPrompt = payload.task.params.user_prompt;
      const projectRoot = payload.task.params.project_root || '/workspace/project';
      const prevResults = payload.loop_state?.previous_results || [];
      const iteration = payload.loop_state?.iteration || 1;

      // Compact LLM-optimized prompt matching SYSTEM_PROMPT.md
      return `SHERATAN AGENT - Respond per SYSTEM_PROMPT protocol.

MISSION: ${userPrompt}
ROOT: ${projectRoot}
ITERATION: ${iteration}
PREVIOUS_RESULTS: ${JSON.stringify(prevResults)}

Actions: list_files{patterns}, read_file{path}, write_file{path,content}
Format: {"ok":true,"action":"create_followup_jobs","new_jobs":[{"name":"X","kind":"...","params":{...}}]}
Done: {"ok":true,"action":"mission_complete","summary":"..."}

Rules: JSON only. Max 5 jobs. Read before write.`;
    }

    // Self-Loop format (Boss directive 2.2)
    if (job.kind === 'self_loop') {
      const mission = payload.mission || {};
      const task = payload.task as any || {};  // Type assertion for name/description
      const state = payload.state || {}; // history_summary, constraints, open_questions

      return `Sheratan Self-Loop (A/B/C/D Format)

Mission:
- Title: ${mission.title || ''}
- Description: ${mission.description || ''}

Current Task:
- Name: ${task.name || ''}
- Description: ${task.description || ''}

Current Loop State (JSON):
${JSON.stringify(state, null, 2)}

Write your answer in EXACTLY this Markdown format:

A) Lagebild / Stand der Dinge
- Kurze, knappe Zusammenfassung der Situation und des Fortschritts.

B) Nächster sinnvoller Schritt
- 1–3 Sätze, was der Agent als nächstes tun sollte.

C) Konkrete Umsetzung (für diese Iteration)
- 3–7 Bulletpoints, sehr konkret, was in dieser Iteration gemacht wird.
- Gern mit Referenzen auf Dateien / Pfade (z.B. project/main.py).

D) Vorschlag für nächsten Loop / offene Fragen
- Bulletpoints mit offenen Fragen oder To-Dos für den nächsten Loop.

WICHTIG:
- Schreibe NUR dieses A/B/C/D-Markdown.
- Kein JSON, keine Erklärungen außerhalb der Sections.
`;
    }    // LCP format tasks
    if (payload.task && payload.mission) {
      const missionGoal = payload.mission.description || payload.mission.goal || 'Complete mission';
      const prevResults = payload.loop_state?.previous_results || [];
      const iteration = payload.loop_state?.iteration || 1;

      // Compact LLM-optimized prompt
      return `SHERATAN AGENT - SYSTEM_PROMPT protocol.

MISSION: ${missionGoal}
ITERATION: ${iteration}
PREVIOUS_RESULTS: ${JSON.stringify(prevResults)}

Actions: list_files{patterns}, read_file{path}, write_file{path,content}
Format: {"ok":true,"action":"create_followup_jobs","new_jobs":[{"name":"X","kind":"...","params":{...}}]}
Done: {"ok":true,"action":"mission_complete","summary":"..."}

JSON only. Max 5 jobs. Read before write.`;
    }

    // Fallback: stringify entire payload
    return `Process this job:
${JSON.stringify(job, null, 2)}

Provide a helpful response ending with }}}`;
  }
}
