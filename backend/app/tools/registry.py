"""Tool registry, Gemini function calling schema definitions, and dispatcher."""

import logging
from typing import Any, Dict, List
from app.models.schemas import Service
from app.storage.base import BaseRepository
from app.tools.deploy import rollback_deploy
from app.tools.github import list_recent_commits, open_github_issue
from app.tools.health import check_health
from app.tools.logs import fetch_logs
from app.agent.runbook_memory import search_similar_runbooks

logger = logging.getLogger("nightwatch.tools.registry")

# Gemini Function Calling Declarations (OpenAPI / JSON Schema format)
TOOL_DEFINITIONS = [
    {
        "name": "fetch_logs",
        "description": "Fetch recent application and error logs from the service, including error stack traces.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "limit": {
                    "type": "INTEGER",
                    "description": "Maximum number of log entries to retrieve (e.g. 20)",
                },
                "level": {
                    "type": "STRING",
                    "description": "Log level filter: 'ERROR', 'WARN', or 'INFO'",
                },
            },
            "required": [],
        },
    },
    {
        "name": "check_health",
        "description": "Actively probe the service health check endpoint and measure round-trip response time.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_recent_commits",
        "description": "List the latest git commits from the service repository to see what changed recently.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "limit": {
                    "type": "INTEGER",
                    "description": "Number of recent commits to check (e.g. 5)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "search_runbooks",
        "description": "Search past incident runbooks for similar symptoms, past root causes, and successful remediation fixes.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Search query describing the symptoms or error message (e.g. 'checkout TypeError discount')",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "propose_rollback",
        "description": "Propose rolling back the service to the previous stable release.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "reason": {
                    "type": "STRING",
                    "description": "Clear reason for rollback citing recent commit or deploy evidence",
                },
            },
            "required": ["reason"],
        },
    },
    {
        "name": "open_github_issue",
        "description": "Create a GitHub issue in the service repository documenting the incident, symptoms, and proposed fix.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {
                    "type": "STRING",
                    "description": "Issue title (e.g. 'Fix TypeError in checkout when discount code is unknown')",
                },
                "body": {
                    "type": "STRING",
                    "description": "Markdown body detailing root cause, logs, and remediation",
                },
            },
            "required": ["title", "body"],
        },
    },
]


async def dispatch_tool_call(
    tool_name: str,
    args: Dict[str, Any],
    service: Service,
    storage: BaseRepository,
) -> Any:
    """Execute a tool call requested by Gemini during investigation."""
    logger.info("Executing agent tool '%s' with args %s for service %s", tool_name, args, service.name)

    if tool_name == "fetch_logs":
        limit = args.get("limit", 25)
        level = args.get("level", "ERROR")
        return await fetch_logs(service, limit=limit, level=level)

    elif tool_name == "check_health":
        return await check_health(service)

    elif tool_name == "list_recent_commits":
        limit = args.get("limit", 5)
        return await list_recent_commits(service, limit=limit)

    elif tool_name == "search_runbooks":
        query = args.get("query", service.name)
        return await search_similar_runbooks(query, storage=storage, limit=3)

    elif tool_name == "propose_rollback":
        return {
            "action": "rollback_deploy",
            "target_service": service.id,
            "reason": args.get("reason", "Recent deployment caused critical error spike"),
            "status": "pending_approval",
        }

    elif tool_name == "open_github_issue":
        title = args.get("title", f"Nightwatch Incident: {service.name} Failure")
        body = args.get("body", "Automated incident report generated by Nightwatch.")
        return await open_github_issue(service, title=title, body=body)

    else:
        return {"error": f"Unknown tool: '{tool_name}'"}
