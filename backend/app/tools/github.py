"""GitHub integration tools for commit inspection and issue creation."""

import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.models.schemas import Service

logger = logging.getLogger("nightwatch.tools.github")


async def list_recent_commits(
    service: Service,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Fetch the latest commits from the service's linked GitHub repository.

    Args:
        service: The service model with githubRepo (e.g. 'owner/repo').
        limit: Max number of recent commits to return.

    Returns:
        List of commit summary dicts (sha, author, message, date).
    """
    repo = service.githubRepo or settings.GITHUB_REPO
    if not repo:
        return [{"error": "No GitHub repository configured for this service"}]

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Nightwatch-OnCall-Agent",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    url = f"https://api.github.com/repos/{repo}/commits"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers=headers, params={"per_page": limit})
            if resp.status_code == 200:
                commits = resp.json()
                results = []
                for c in commits:
                    commit_data = c.get("commit", {})
                    author_data = commit_data.get("author", {})
                    results.append({
                        "sha": c.get("sha", "")[:7],
                        "full_sha": c.get("sha", ""),
                        "author": author_data.get("name", "Unknown"),
                        "date": author_data.get("date", ""),
                        "message": commit_data.get("message", "").split("\n")[0],
                    })
                return results
            logger.warning("GitHub API returned HTTP %d for %s", resp.status_code, repo)
            return [{"error": f"GitHub API error HTTP {resp.status_code}: {resp.text[:100]}"}]
    except Exception as exc:
        logger.error("Failed to fetch GitHub commits for %s: %s", repo, exc)
        return [{"error": f"Failed to connect to GitHub: {exc}"}]


async def open_github_issue(
    service: Service,
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new GitHub issue with incident evidence and diagnosis.

    Args:
        service: The service model.
        title: Issue title.
        body: Markdown body.
        labels: Optional label names (e.g. ['bug', 'nightwatch']).

    Returns:
        Dict with issue number, HTML URL, and status.
    """
    repo = service.githubRepo or settings.GITHUB_REPO
    if not repo:
        return {"success": False, "error": "No GitHub repository configured"}

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Nightwatch-OnCall-Agent",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    url = f"https://api.github.com/repos/{repo}/issues"
    payload: Dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "success": True,
                    "issue_number": data.get("number"),
                    "html_url": data.get("html_url"),
                    "title": title,
                }
            return {
                "success": False,
                "error": f"GitHub API HTTP {resp.status_code}: {resp.text[:150]}",
            }
    except Exception as exc:
        return {"success": False, "error": str(exc)}
