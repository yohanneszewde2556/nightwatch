"""In-memory structured JSON log ring buffer.

Stores the last N log entries (default 1000) in a deque.
Each entry is a LogEntry with timestamp, level, request_id, route,
status code, latency_ms, version, and optional exception traceback.
"""
import threading
from collections import deque
from datetime import datetime, timezone
from app.models import LogEntry


class LogBuffer:
    """Thread-safe ring buffer for structured log entries."""

    def __init__(self, max_size: int = 1000) -> None:
        self._buffer: deque[LogEntry] = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def add(
        self,
        level: str,
        request_id: str,
        route: str,
        status: int,
        latency_ms: float,
        version: str,
        exception: str | None = None,
    ) -> None:
        """Add a log entry to the buffer."""
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            request_id=request_id,
            route=route,
            status=status,
            latency_ms=latency_ms,
            version=version,
            exception=exception,
        )
        with self._lock:
            self._buffer.append(entry)

    def query(
        self,
        level: str | None = None,
        since: str | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        """Query log entries with optional filters.

        Args:
            level: Filter by log level (INFO, WARN, ERROR).
            since: ISO timestamp; return entries after this time.
            limit: Maximum number of entries to return.

        Returns:
            List of matching log entries, most recent first.
        """
        with self._lock:
            entries = list(self._buffer)

        # Filter by level
        if level:
            entries = [e for e in entries if e.level.upper() == level.upper()]

        # Filter by since timestamp
        if since:
            entries = [e for e in entries if e.timestamp >= since]

        # Most recent first, apply limit
        entries.reverse()
        return entries[:limit]

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._buffer.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)


# Global log buffer instance
log_buffer = LogBuffer()
