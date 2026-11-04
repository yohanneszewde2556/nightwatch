"""Agent tools module.

Implements tools available to the Nightwatch agent:
- fetch_logs: Cloud Run logging
- check_health: HTTP health endpoint probe
- list_recent_commits: GitHub commit and deployment history
- search_runbooks: Semantic vector search over past fixes
- open_github_issue: GitHub issue creation
- create_fix_pr: Draft pull request generation
- rollback_deploy: Cloud Run revision traffic shift
- notify: Telegram alert dispatcher
Implementation scheduled for Phase 3.
"""
