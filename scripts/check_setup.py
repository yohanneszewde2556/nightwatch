#!/usr/bin/env python3
"""Nightwatch Environment & Integration Setup Check Script.

Tests connectivity and credentials for:
a) Gemini API
b) GitHub API (repo & issues)
c) Telegram Bot API (getMe & sendMessage)
d) SQLite Storage (write & read back)

Never prints secret values in cleartext.
"""

import json
import os
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

# Set UTF-8 encoding for standard streams on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPO_ROOT / ".env"
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE)
    except ImportError:
        # Fallback simple .env reader if python-dotenv is not installed
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))

from app.core.config import settings
from app.core.gemini_client import (
    GeminiConfigError,
    GeminiError,
    get_gemini_client,
)


def mask_secret(value: Optional[str]) -> str:
    """Mask secret value showing only the last 4 characters."""
    if not value or not value.strip():
        return "(not set)"
    v = value.strip()
    if len(v) <= 4:
        return "****"
    return f"{'*' * (len(v) - 4)}{v[-4:]}"


def test_gemini() -> Tuple[str, str]:
    """Test Gemini AI by sending a minimal generateContent request using shared GeminiClient."""
    if not settings.GEMINI_API_KEY:
        return "SKIPPED", f"GEMINI_API_KEY is not set (configured model: {settings.GEMINI_MODEL})"

    try:
        client = get_gemini_client()
        resp = client.generate_content("Reply with only the word 'ready'.", max_output_tokens=10)
        return (
            "PASS",
            f"Model '{resp.model}' answered in {resp.duration_seconds:.2f}s: {resp.text[:30]}",
        )
    except GeminiConfigError as e:
        return "SKIPPED", str(e)
    except GeminiError as e:
        return "FAIL", str(e)
    except Exception as e:
        return "FAIL", f"Unexpected error: {str(e)}"


def test_github() -> Tuple[str, str]:
    """Test GitHub token access and repository issues readability."""
    token = (settings.GITHUB_TOKEN or "").strip()
    repo = (settings.GITHUB_REPO or "").strip()

    if not token or not repo:
        missing = []
        if not token:
            missing.append("GITHUB_TOKEN")
        if not repo:
            missing.append("GITHUB_REPO")
        return "SKIPPED", f"{', '.join(missing)} not set"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Nightwatch-Setup-Check",
    }

    # 1. Check repo accessibility
    repo_url = f"https://api.github.com/repos/{repo}"
    req_repo = urllib.request.Request(repo_url, headers=headers)
    try:
        with urllib.request.urlopen(req_repo, timeout=10.0) as resp:
            repo_data = json.loads(resp.read().decode("utf-8"))
            repo_name = repo_data.get("full_name", repo)
    except urllib.error.HTTPError as e:
        return "FAIL", f"Failed reading repo {repo} (HTTP {e.code}: {e.reason})"
    except Exception as e:
        return "FAIL", f"GitHub repo connection error: {str(e)}"

    # 2. Check issues reading capability
    issues_url = f"https://api.github.com/repos/{repo}/issues?per_page=1"
    req_issues = urllib.request.Request(issues_url, headers=headers)
    try:
        with urllib.request.urlopen(req_issues, timeout=10.0) as resp:
            return "PASS", f"Repo '{repo_name}' accessible with issues read permission"
    except urllib.error.HTTPError as e:
        return "FAIL", f"Cannot read issues for {repo} (HTTP {e.code}: {e.reason})"
    except Exception as e:
        return "FAIL", f"GitHub issues error: {str(e)}"


def test_telegram() -> Tuple[str, str]:
    """Test Telegram Bot API getMe and optional test message send."""
    bot_token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    chat_id = (settings.TELEGRAM_CHAT_ID or "").strip()

    if not bot_token:
        return "SKIPPED", "TELEGRAM_BOT_TOKEN is not set"

    # 1. getMe
    get_me_url = f"https://api.telegram.org/bot{bot_token}/getMe"
    try:
        with urllib.request.urlopen(get_me_url, timeout=10.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not data.get("ok"):
                return "FAIL", f"getMe returned false: {data.get('description')}"
            username = data.get("result", {}).get("username", "unknown")
    except urllib.error.HTTPError as e:
        return "FAIL", f"Bot auth failed (HTTP {e.code}: {e.reason})"
    except Exception as e:
        return "FAIL", f"Telegram getMe connection error: {str(e)}"

    # 2. sendMessage if chat_id is present
    if not chat_id:
        return "PASS", f"Bot @{username} verified. TELEGRAM_CHAT_ID not set, skipped message send."

    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🛡️ Nightwatch setup check: integration connectivity test verified.",
    }
    req = urllib.request.Request(
        send_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            send_data = json.loads(resp.read().decode("utf-8"))
            if send_data.get("ok"):
                return "PASS", f"Bot @{username} sent test alert to chat {mask_secret(chat_id)}"
            return "FAIL", f"sendMessage error: {send_data.get('description')}"
    except urllib.error.HTTPError as e:
        return "FAIL", f"sendMessage failed (HTTP {e.code}: {e.reason})"
    except Exception as e:
        return "FAIL", f"sendMessage error: {str(e)}"


def test_sqlite_storage() -> Tuple[str, str]:
    """Create and read back one record in the SQLite database."""
    db_path = os.getenv("SQLITE_DB_PATH", "").strip()
    if not db_path:
        db_path = str(REPO_ROOT / "nightwatch.db")

    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS _setup_check (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            );
        """)
        test_id = "test-probe-1"
        cursor.execute("INSERT OR REPLACE INTO _setup_check (id, created_at) VALUES (?, datetime('now'))", (test_id,))
        conn.commit()

        cursor.execute("SELECT id, created_at FROM _setup_check WHERE id = ?", (test_id,))
        row = cursor.fetchone()
        if not row or row[0] != test_id:
            conn.close()
            return "FAIL", "Record write verification failed"

        cursor.execute("DELETE FROM _setup_check WHERE id = ?", (test_id,))
        conn.commit()
        conn.close()
        return "PASS", f"Read & write verified on SQLite DB ({Path(db_path).name})"
    except Exception as e:
        return "FAIL", f"SQLite error: {str(e)}"


def main() -> int:
    print("=" * 70)
    print("             NIGHTWATCH SETUP & INTEGRATION CHECK              ")
    print("=" * 70)
    print(f"Loaded config from: {ENV_FILE if ENV_FILE.exists() else 'System Environment'}")
    print()

    # Secret masking preview
    print("Configured Credentials (Masked):")
    print(f"  * GEMINI_API_KEY:         {mask_secret(settings.GEMINI_API_KEY)}")
    print(f"  * GEMINI_MODEL:           {settings.GEMINI_MODEL}")
    print(f"  * GEMINI_FALLBACK_MODELS: {settings.GEMINI_FALLBACK_MODELS or '(none)'}")
    print(f"  * GEMINI_TIMEOUT_SECONDS: {settings.GEMINI_TIMEOUT_SECONDS}s")
    print(f"  * GITHUB_TOKEN:           {mask_secret(settings.GITHUB_TOKEN)}")
    print(f"  * GITHUB_REPO:            {settings.GITHUB_REPO or '(not set)'}")
    print(f"  * TELEGRAM_BOT_TOKEN:     {mask_secret(settings.TELEGRAM_BOT_TOKEN)}")
    print(f"  * TELEGRAM_CHAT_ID:       {mask_secret(settings.TELEGRAM_CHAT_ID)}")
    print(f"  * DASHBOARD_PASSWORD:     {mask_secret(settings.DASHBOARD_PASSWORD)}")
    print(f"  * TICK_SECRET:            {mask_secret(settings.TICK_SECRET)}")
    print(f"  * STORAGE_BACKEND:        {settings.STORAGE_BACKEND}")
    print("-" * 70)
    print()

    tests = [
        ("Storage (SQLite)", test_sqlite_storage),
        ("Gemini AI API", test_gemini),
        ("GitHub REST API", test_github),
        ("Telegram Bot API", test_telegram),
    ]

    has_failures = False
    for name, test_fn in tests:
        status, details = test_fn()
        if status == "PASS":
            badge = "[PASS]   "
        elif status == "SKIPPED":
            badge = "[SKIPPED]"
        else:
            badge = "[FAIL]   "
            has_failures = True
        print(f"{badge} {name:<20} {details}")

    print()
    print("=" * 70)
    if has_failures:
        print("[!] One or more configured integrations failed. See details above.")
        return 1
    else:
        print("[OK] Setup check completed cleanly. All tested components operational.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
