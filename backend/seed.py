"""Database seed runner script."""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.storage import get_repository, seed_database


def main() -> None:
    print("[*] Seeding Nightwatch database with sample services and incidents...")
    storage = get_repository()
    # Check if services already exist
    existing = storage.list_services()
    if existing:
        print(f"[*] Database already contains {len(existing)} services. Skipping re-seed.")
        return

    seed_database(storage)
    print("[OK] Database successfully seeded.")


if __name__ == "__main__":
    main()
