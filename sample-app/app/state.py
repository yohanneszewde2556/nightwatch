"""In-memory runtime state for demo-shop."""
import time
from app.config import settings


COMMIT_LABELS = {
    "v1": "Initial demo-shop API",
    "v2": "Add discount codes to checkout",
}


class AppState:
    """Thread-safe runtime state."""

    def __init__(self) -> None:
        self.version: str = settings.APP_VERSION
        self.chaos_mode: str = settings.CHAOS_MODE
        self.commit_label: str = COMMIT_LABELS.get(self.version, "Initial demo-shop API")
        self.start_time: float = time.time()
        self.slow_counter: int = 0

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.start_time

    def deploy(self, version: str) -> None:
        self.version = version
        self.commit_label = COMMIT_LABELS.get(version, f"Release {version}")

    def rollback(self) -> None:
        self.version = "v1"
        self.commit_label = COMMIT_LABELS["v1"]

    def set_chaos(self, mode: str) -> None:
        self.chaos_mode = mode
        if mode != "slow":
            self.slow_counter = 0

    def next_slow_delay(self) -> float:
        """Calculate next growing delay up to ~6.0 seconds."""
        self.slow_counter += 1
        # Gradually increase delay: 0.5s + counter * 0.4s capped at 6.0s
        return min(6.0, 0.5 + self.slow_counter * 0.4)

    def reset(self) -> None:
        """Reset state to default v1 for testing."""
        self.version = "v1"
        self.chaos_mode = "none"
        self.commit_label = COMMIT_LABELS["v1"]
        self.slow_counter = 0
        self.start_time = time.time()


state = AppState()
