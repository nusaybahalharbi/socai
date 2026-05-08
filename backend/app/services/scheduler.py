"""APScheduler-based background poller.

Runs in-process inside FastAPI. Every SPLUNK_POLL_INTERVAL_SECONDS it pulls
new alerts from Splunk (or mock connector) and runs them through ingestion.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.connectors.mock_connector import MockConnector
from app.connectors.splunk_connector import SplunkConnector
from app.db.session import SessionLocal
from app.services.ingestion import ingest_batch

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _poll_once() -> None:
    db = SessionLocal()
    try:
        if settings.DATA_MODE == "splunk":
            connector = SplunkConnector()
            n = ingest_batch(db, connector.fetch_alerts())
            logger.info("[poll] Splunk -> ingested %d new alerts", n)
        else:
            connector = MockConnector()
            n = ingest_batch(db, connector.fetch_alerts())
            logger.info("[poll] Mock -> ingested %d new alerts", n)
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    interval = settings.SPLUNK_POLL_INTERVAL_SECONDS if settings.DATA_MODE == "splunk" else settings.MOCK_ALERT_INTERVAL_SECONDS
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(_poll_once, "interval", seconds=interval, id="alert_poll", max_instances=1)
    _scheduler.start()
    logger.info("[scheduler] started in %s mode every %ds", settings.DATA_MODE, interval)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
