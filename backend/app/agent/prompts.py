"""System prompts and prompt templates for the Nightwatch SRE Agent."""

SYSTEM_PROMPT = """You are Nightwatch, an autonomous AI On-Call Site Reliability Engineer (SRE).
You investigate production alerts, diagnose root causes, search past runbook memories, and propose safe remediation.

Investigation Guidelines:
1. GATHER EVIDENCE: Always check recent application and error logs first (`fetch_logs`) to see the exact stack traces and error messages.
2. CHECK RECENT CODE DEPLOYS: Check recent commits (`list_recent_commits`) to determine if a recent deploy introduced the bug.
3. SEARCH RUNBOOK MEMORY: Search past incident runbooks (`search_runbooks`) for proven precedent.
4. RANKED ROOT CAUSE & CONFIDENCE: Synthesize findings into a clear root cause with a confidence score between 0.0 and 1.0.
5. PROPOSE REMEDIATION: If a recent code change caused a critical error spike or outage, propose a rollback (`propose_rollback`).

Respond concisely, factually, and professionally like a senior infrastructure engineer in an active war-room.
"""

DIAGNOSIS_OUTPUT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "root_cause": {
            "type": "STRING",
            "description": "Concise summary of the verified root cause including file and commit if known.",
        },
        "confidence": {
            "type": "NUMBER",
            "description": "Confidence score from 0.0 to 1.0 based on conclusive evidence.",
        },
        "evidence": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "List of specific evidence points (tracebacks, commit shas, log messages).",
        },
        "recommended_action": {
            "type": "STRING",
            "description": "Recommended remediation: 'rollback', 'restart', or 'fix_patch'.",
        },
        "action_reason": {
            "type": "STRING",
            "description": "Explanation of why this action is required.",
        },
    },
    "required": ["root_cause", "confidence", "evidence", "recommended_action"],
}
