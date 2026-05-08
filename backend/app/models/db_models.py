"""ORM models for the SOC AI platform."""
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Float, DateTime, ForeignKey, JSON, Text, Boolean, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="analyst")  # analyst, lead, admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(128), index=True)  # Splunk event id or mock uuid
    source: Mapped[str] = mapped_column(String(32), default="splunk")  # splunk | mock
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(16), default="medium")  # low/medium/high/critical
    raw_event: Mapped[dict] = mapped_column(JSON, default=dict)

    # Common normalized fields used as ML features
    src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dst_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user: Mapped[str | None] = mapped_column(String(128), nullable=True)
    host: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    process_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    command_line: Mapped[str | None] = mapped_column(Text, nullable=True)
    hour_of_day: Mapped[int] = mapped_column(Integer, default=0)
    is_off_hours: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[str] = mapped_column(String(32), default="new")  # new/triaged/closed/escalated
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    prediction: Mapped["Prediction | None"] = relationship(
        back_populates="alert", uselist=False, cascade="all, delete-orphan"
    )
    mitre_mappings: Mapped[list["MitreMapping"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )
    feedback: Mapped[list["AnalystFeedback"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_alerts_status_ingested", "status", "ingested_at"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), unique=True)
    label: Mapped[str] = mapped_column(String(32))  # threat | false_positive
    confidence: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(32), default="v1")
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)  # SHAP-style top features
    recommendation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    alert: Mapped["Alert"] = relationship(back_populates="prediction")


class MitreMapping(Base):
    __tablename__ = "mitre_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"))
    tactic: Mapped[str] = mapped_column(String(64))
    technique_id: Mapped[str] = mapped_column(String(16), index=True)
    technique_name: Mapped[str] = mapped_column(String(128))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    rationale: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    alert: Mapped["Alert"] = relationship(back_populates="mitre_mappings")


class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision: Mapped[str] = mapped_column(String(32))  # confirm_threat/false_positive/escalate/needs_review
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    alert: Mapped["Alert"] = relationship(back_populates="feedback")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    target: Mapped[str] = mapped_column(String(128), default="")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
