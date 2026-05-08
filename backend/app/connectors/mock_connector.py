"""Mock connector: yields synthetic alerts when DATA_MODE=mock."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Any

from app.core.config import settings
from app.ml.synthetic import generate_live_batch


class MockConnector:
    def fetch_alerts(self) -> Iterable[dict[str, Any]]:
        for a in generate_live_batch(n=settings.MOCK_ALERTS_PER_BATCH):
            # ensure datetime objects, not strings, for ORM
            if isinstance(a.get("occurred_at"), str):
                try:
                    a["occurred_at"] = datetime.fromisoformat(a["occurred_at"])
                except Exception:
                    a["occurred_at"] = datetime.now(timezone.utc)
            yield a
