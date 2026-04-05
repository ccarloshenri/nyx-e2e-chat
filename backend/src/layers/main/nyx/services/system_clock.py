from datetime import UTC, datetime

from src.layers.main.nyx.interfaces.services.i_clock import IClock


class SystemClock(IClock):
    def now(self) -> datetime:
        return datetime.now(UTC)

    def now_iso(self) -> str:
        return self.now().isoformat()
