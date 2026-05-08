"""Alerts, predictions, MITRE, feedback, metrics endpoints."""
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.db_models import Alert, AnalystFeedback, MitreMapping, Prediction, User
from app.schemas.schemas import (
    AlertIn, AlertListResponse, AlertOut, FeedbackIn, MetricsOverview
)
from app.services.ingestion import ingest_one

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _alert_q(db: Session):
    return (
        db.query(Alert)
        .options(selectinload(Alert.prediction), selectinload(Alert.mitre_mappings))
    )


@router.get("", response_model=AlertListResponse)
def list_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status_filter: str | None = Query(None, alias="status"),
    label: str | None = Query(None),
    severity: str | None = Query(None),
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = _alert_q(db)
    if status_filter:
        q = q.filter(Alert.status == status_filter)
    if severity:
        q = q.filter(Alert.severity == severity)
    if label or min_confidence is not None:
        q = q.join(Prediction)
        if label:
            q = q.filter(Prediction.label == label)
        if min_confidence is not None:
            q = q.filter(Prediction.confidence >= min_confidence)
    total = q.count()
    items = q.order_by(Alert.ingested_at.desc()).offset(offset).limit(limit).all()
    return AlertListResponse(total=total, items=items)


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alert = _alert_q(db).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    return alert


@router.post("/ingest", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def ingest_alert(body: AlertIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Manual ingestion endpoint (used by tests, by Splunk webhook, or for demos)."""
    raw = body.model_dump()
    alert = ingest_one(db, raw)
    if not alert:
        # duplicate — return the existing record
        existing = _alert_q(db).filter(Alert.source_id == body.source_id).first()
        if existing:
            return existing
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Failed to ingest alert")
    # reload with relationships eager-loaded
    return _alert_q(db).filter(Alert.id == alert.id).first()


@router.post("/{alert_id}/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    alert_id: int,
    body: FeedbackIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")

    valid = {"confirm_threat", "false_positive", "escalate", "needs_review"}
    if body.decision not in valid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"decision must be one of {valid}")

    fb = AnalystFeedback(
        alert_id=alert.id,
        user_id=user.id,
        decision=body.decision,
        notes=body.notes,
    )
    # update alert status
    alert.status = {
        "confirm_threat": "triaged",
        "false_positive": "closed",
        "escalate": "escalated",
        "needs_review": "triaged",
    }[body.decision]

    db.add(fb)
    db.commit()
    return {"ok": True, "alert_status": alert.status}


# ---------------- Metrics ----------------
metrics_router = APIRouter(prefix="/metrics", tags=["metrics"])


@metrics_router.get("/overview", response_model=MetricsOverview)
def metrics_overview(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    window_hours: int = Query(24, ge=1, le=24 * 30),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    total = db.query(func.count(Alert.id)).filter(Alert.ingested_at >= cutoff).scalar() or 0
    threats = (
        db.query(func.count(Prediction.id))
        .join(Alert, Alert.id == Prediction.alert_id)
        .filter(Alert.ingested_at >= cutoff, Prediction.label == "threat")
        .scalar() or 0
    )
    fps = (
        db.query(func.count(Prediction.id))
        .join(Alert, Alert.id == Prediction.alert_id)
        .filter(Alert.ingested_at >= cutoff, Prediction.label == "false_positive")
        .scalar() or 0
    )
    open_alerts = (
        db.query(func.count(Alert.id))
        .filter(Alert.ingested_at >= cutoff, Alert.status == "new")
        .scalar() or 0
    )
    avg_conf = (
        db.query(func.avg(Prediction.confidence))
        .join(Alert, Alert.id == Prediction.alert_id)
        .filter(Alert.ingested_at >= cutoff)
        .scalar()
    ) or 0.0

    by_sev_rows = (
        db.query(Alert.severity, func.count(Alert.id))
        .filter(Alert.ingested_at >= cutoff)
        .group_by(Alert.severity).all()
    )
    by_sev = {sev or "unknown": int(c) for sev, c in by_sev_rows}

    by_et_rows = (
        db.query(Alert.event_type, func.count(Alert.id))
        .filter(Alert.ingested_at >= cutoff)
        .group_by(Alert.event_type).all()
    )
    by_et = {et or "unknown": int(c) for et, c in by_et_rows}

    fp_pct = (fps / total * 100.0) if total else 0.0
    return MetricsOverview(
        total_alerts=total,
        threats=int(threats),
        false_positives=int(fps),
        open_alerts=int(open_alerts),
        avg_confidence=float(avg_conf),
        by_severity=by_sev,
        by_event_type=by_et,
        fp_reduction_estimate_pct=round(fp_pct, 1),
    )
