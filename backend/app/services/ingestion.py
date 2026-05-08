"""Alert ingestion pipeline.

For each incoming alert dict:
 1. persist to alerts table (skip duplicates by source_id)
 2. classify with ML model (label, confidence, SHAP)
 3. map to MITRE ATT&CK techniques
 4. build SOC recommendation
 5. persist prediction + mappings
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.models.db_models import Alert, MitreMapping, Prediction
from app.mitre.engine import get_mitre_engine
from app.ml.inference import build_recommendation, get_classifier

logger = logging.getLogger(__name__)


def _ensure_normalized(a: dict[str, Any]) -> dict[str, Any]:
    """Make sure required fields exist with sane defaults."""
    occurred = a.get("occurred_at")
    if occurred is None:
        occurred = datetime.now(timezone.utc)
        a["occurred_at"] = occurred
    if isinstance(occurred, datetime):
        a.setdefault("hour_of_day", occurred.hour)
        a.setdefault("is_off_hours", occurred.hour < 6 or occurred.hour >= 22)
    a.setdefault("severity", "medium")
    a.setdefault("description", "")
    a.setdefault("title", a.get("event_type", "alert").replace("_", " ").title())
    a.setdefault("source", "unknown")
    a.setdefault("raw_event", {})
    a.setdefault("failed_login_count", 0)
    return a


def ingest_one(db: Session, raw: dict[str, Any]) -> Alert | None:
    """Process a single alert dict end-to-end. Returns the persisted Alert (or None if skipped)."""
    a = _ensure_normalized(dict(raw))

    # de-dup
    existing = db.query(Alert).filter(Alert.source_id == a["source_id"]).first()
    if existing:
        return None

    alert = Alert(
        source_id=a["source_id"],
        source=a["source"],
        title=a["title"],
        description=a.get("description", ""),
        severity=a["severity"],
        raw_event=a.get("raw_event", {}),
        src_ip=a.get("src_ip"),
        dst_ip=a.get("dst_ip"),
        user=a.get("user"),
        host=a.get("host"),
        event_type=a.get("event_type"),
        failed_login_count=int(a.get("failed_login_count") or 0),
        process_name=a.get("process_name"),
        command_line=a.get("command_line"),
        hour_of_day=int(a.get("hour_of_day") or 0),
        is_off_hours=bool(a.get("is_off_hours")),
        occurred_at=a["occurred_at"],
    )
    db.add(alert)
    db.flush()  # need alert.id

    # Classification
    clf = get_classifier()
    label, confidence, explanation = clf.predict(a)

    # MITRE
    mitre = get_mitre_engine().map_alert(a)

    # Recommendation
    rec = build_recommendation(a, label, mitre)

    pred = Prediction(
        alert_id=alert.id,
        label=label,
        confidence=confidence,
        model_version=(clf.bundle or {}).get("version", "heuristic-v0"),
        explanation=explanation,
        recommendation=rec,
    )
    db.add(pred)

    for h in mitre:
        db.add(MitreMapping(
            alert_id=alert.id,
            tactic=h.tactic,
            technique_id=h.technique_id,
            technique_name=h.technique_name,
            confidence=h.confidence,
            rationale=h.rationale,
        ))

    db.commit()
    db.refresh(alert)
    return alert


def ingest_batch(db: Session, alerts: Iterable[dict[str, Any]]) -> int:
    n = 0
    for raw in alerts:
        try:
            if ingest_one(db, raw):
                n += 1
        except Exception:
            logger.exception("Failed to ingest alert: %s", raw.get("source_id"))
            db.rollback()
    return n
