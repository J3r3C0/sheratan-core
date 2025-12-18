// ========================================
// Sheratan WebRelay - Response Parser
// ========================================

import { ParseResult, LCPAction } from './types.js';

/**
 * Strip sentinel marker from end of response
 */
export function stripSentinel(text: string, sentinel: string): string {
    if (text.endsWith(sentinel)) {
        return text.slice(0, -sentinel.length).trimEnd();
    }
    return text;
}

/**
 * Try to extract JSON from markdown code block or find JSON in mixed text
 */
function extractJsonFromMarkdown(text: string): string | null {
    // Try markdown code block first
    const codeBlockMatch = text.match(/```(?:json)?\s*\n?([\s\S]*?)\n?```/);
    if (codeBlockMatch) {
        return codeBlockMatch[1].trim();
    }

    // Find the first '{' that starts a complete JSON object
    let depth = 0;
    let startIdx = -1;

    for (let i = 0; i < text.length; i++) {
        if (text[i] === '{') {
            if (depth === 0) startIdx = i;
            depth++;
        } else if (text[i] === '}') {
            depth--;
            if (depth === 0 && startIdx !== -1) {
                // Found a complete JSON object
                return text.slice(startIdx, i + 1);
            }
        }
    }

    return null;
}

/**
 * Parse LLM response - auto-detect LCP format or return plain text
 */
export function parseResponse(rawAnswer: string, config: { sentinel: string }): ParseResult {
    // Strip sentinel first
    const cleaned = stripSentinel(rawAnswer, config.sentinel);

    // Try to find JSON in response
    let jsonText = extractJsonFromMarkdown(cleaned);
    if (!jsonText) {
        // Try direct JSON parse
        jsonText = cleaned.trim();
    }

    // Try to parse as LCP JSON
    try {
        const parsed = JSON.parse(jsonText);

        // Check if it's LCP format (has actions array)
        if (parsed.actions && Array.isArray(parsed.actions)) {
            return {
                type: 'lcp',
                thought: parsed.thought || '',
                actions: parsed.actions as LCPAction[],
            };
        }

        // Check if it's an LCP action (create_followup_jobs, mission_complete, etc.)
        const lcpActions = ['create_followup_jobs', 'mission_complete', 'analysis_result'];
        if (parsed.action && (lcpActions.includes(parsed.action) || parsed.new_jobs)) {
            return {
                type: 'lcp',
                action: parsed.action,
                commentary: parsed.commentary || parsed.summary || '',
                new_jobs: parsed.new_jobs || [],
            };
        }

        // Some other JSON format - treat as text
        return {
            type: 'text',
            summary: JSON.stringify(parsed, null, 2),
        };
    } catch (e) {
        // Not valid JSON - return as plain text
        return {
            type: 'text',
            summary: cleaned,
        };
    }
}
