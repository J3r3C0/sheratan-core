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

    // agent_plan or general LCP format
    if (job.kind === 'agent_plan' || (payload.task && payload.mission)) {
      const userPrompt = payload.task?.params?.user_prompt || payload.mission?.description || 'Continue mission';
      const projectRoot = payload.task?.params?.project_root || payload.params?.root || 'C:/workspace';
      const prevResults = payload.loop_state?.previous_results || [];
      const iteration = payload.loop_state?.iteration || 1;

      // Extremely concise protocol-driven prompt
      return `SHERATAN PROTOCOL - ACT NOW
MISSION: ${userPrompt}
ROOT: ${projectRoot}
ITERATION: ${iteration}
CONTEXT: ${JSON.stringify(prevResults)}

RULES:
1. Respond with VALID JSON only (no intro/outro)
2. Use "create_followup_jobs" to continue (list_files, read_file, rewrite_file)
3. Use "mission_complete" to finish
4. Limit to 3 jobs max per turn.

JSON RESPONSE:`;
    }

    // Self-Loop format (Boss directive 2.2)
    if (job.kind === 'self_loop') {
      const mission = payload.mission || {};
      const task = payload.task as any || {};
      const state = payload.state || {};

      return `Sheratan Self-Loop Report
Mission: ${mission.title || ''} (${mission.description || ''})
Task: ${task.name || ''} (${task.description || ''})
State: ${JSON.stringify(state)}

Markdown Format:
A) Lagebild
B) Nächster Schritt
C) Umsetzung (3-5 Bullets)
D) Offene Fragen

RESPOND NOW (Markdown only):`;
    }

    // Fallback
    return `Process job kind "${job.kind}": ${JSON.stringify(job.payload)}`;
  }
}
