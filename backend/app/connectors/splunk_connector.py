"""Splunk integration: pull events via the Splunk SDK and normalize them.

The connector runs a configurable SPL search ("savedsearch" or raw) and
yields normalized alert dicts ready for the ingestion pipeline.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable

import splunklib.client as splunk_client
import splunklib.results as splunk_results

from app.core.config import settings

logger = logging.getLogger(__name__)


# A reasonable default search if the user hasn't created a saved search yet.
DEFAULT_SEARCH = (
    'search index={index} earliest=-{interval}s '
    '(EventCode=4625 OR EventCode=4624 OR sourcetype="WinEventLog:Security" '
    'OR sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational") '
    '| head 200'
)


def _to_str(v: Any) -> str | None:
    if v is None:
        return None
    return str(v)


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Turn a raw Splunk event dict into our canonical alert shape."""
    et = (event.get("EventCode") or event.get("eventcode") or "").strip()
    event_type = {
        "4625": "failed_login",
        "4624": "successful_login",
        "1": "process_create",
        "3": "network_connection",
        "11": "file_create",
        "13": "registry_modification",
    }.get(et, "other")

    cmd = event.get("CommandLine") or event.get("command_line")
    proc = event.get("Image") or event.get("ProcessName") or event.get("process_name")
    src_ip = event.get("src_ip") or event.get("IpAddress") or event.get("SourceIp")
    dst_ip = event.get("dst_ip") or event.get("DestinationIp")
    user = event.get("TargetUserName") or event.get("user") or event.get("User")
    host = event.get("Computer") or event.get("host")

    occurred = event.get("_time")
    try:
        occurred_dt = datetime.fromisoformat(occurred) if occurred else datetime.now(timezone.utc)
    except Exception:
        occurred_dt = datetime.now(timezone.utc)

    failed = 0
    if event_type == "failed_login":
        # If the search aggregates with stats count, Splunk returns "count"
        try:
            failed = int(event.get("count") or 1)
        except (TypeError, ValueError):
            failed = 1

    severity = "high" if event_type in ("failed_login",) and failed >= 10 else "medium"

    return {
        "source_id": event.get("_cd") or event.get("_serial") or f"splunk-{occurred_dt.isoformat()}-{user or ''}",
        "source": "splunk",
        "title": f"{event_type.replace('_', ' ').title()} ({et})" if et else event_type.replace("_", " ").title(),
        "description": event.get("_raw", "")[:500],
        "severity": severity,
        "raw_event": event,
        "src_ip": _to_str(src_ip),
        "dst_ip": _to_str(dst_ip),
        "user": _to_str(user),
        "host": _to_str(host),
        "event_type": event_type,
        "failed_login_count": failed,
        "process_name": _to_str(proc),
        "command_line": _to_str(cmd),
        "occurred_at": occurred_dt,
        "hour_of_day": occurred_dt.hour,
        "is_off_hours": occurred_dt.hour < 6 or occurred_dt.hour >= 22,
    }


class SplunkConnector:
    def __init__(self):
        self._service: splunk_client.Service | None = None

    def _connect(self) -> splunk_client.Service:
        if self._service is None:
            logger.info("Connecting to Splunk at %s:%s", settings.SPLUNK_HOST, settings.SPLUNK_PORT)
            self._service = splunk_client.connect(
                host=settings.SPLUNK_HOST,
                port=settings.SPLUNK_PORT,
                username=settings.SPLUNK_USERNAME,
                password=settings.SPLUNK_PASSWORD,
                scheme=settings.SPLUNK_SCHEME,
                verify=settings.SPLUNK_VERIFY_SSL,
            )
        return self._service

    def fetch_alerts(self, search: str | None = None) -> Iterable[dict[str, Any]]:
        """Run a oneshot search and yield normalized alert dicts."""
        try:
            service = self._connect()
        except Exception as e:
            logger.error("Splunk connect failed: %s", e)
            return

        spl = search or DEFAULT_SEARCH.format(
            index=settings.SPLUNK_INDEX,
            interval=settings.SPLUNK_POLL_INTERVAL_SECONDS,
        )
        logger.info("Running SPL: %s", spl)
        try:
            kwargs = {"output_mode": "json", "count": 0}
            stream = service.jobs.oneshot(spl, **kwargs)
            reader = splunk_results.JSONResultsReader(stream)
            for item in reader:
                if isinstance(item, dict):
                    yield _normalize_event(item)
        except Exception as e:
            logger.exception("Splunk search failed: %s", e)
            return
