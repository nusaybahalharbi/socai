"""Pydantic API schemas."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


# ---------------- Auth ----------------
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    role: str
    is_active: bool


# ---------------- Alerts ----------------
class AlertIn(BaseModel):
    """Inbound alert from Splunk or external source."""
    source_id: str
    source: str = "splunk"
    title: str
    description: str = ""
    severity: str = "medium"
    raw_event: dict[str, Any] = Field(default_factory=dict)
    src_ip: str | None = None
    dst_ip: str | None = None
    user: str | None = None
    host: str | None = None
    event_type: str | None = None
    failed_login_count: int = 0
    process_name: str | None = None
    command_line: str | None = None
    occurred_at: datetime | None = None


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    label: str
    confidence: float
    model_version: str
    explanation: dict[str, Any]
    recommendation: str


class MitreMappingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tactic: str
    technique_id: str
    technique_name: str
    confidence: float
    rationale: str


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_id: str
    source: str
    title: str
    description: str
    severity: str
    src_ip: str | None
    dst_ip: str | None
    user: str | None
    host: str | None
    event_type: str | None
    failed_login_count: int
    process_name: str | None
    command_line: str | None
    status: str
    occurred_at: datetime
    ingested_at: datetime
    prediction: PredictionOut | None = None
    mitre_mappings: list[MitreMappingOut] = Field(default_factory=list)


class AlertListResponse(BaseModel):
    total: int
    items: list[AlertOut]


# ---------------- Feedback ----------------
class FeedbackIn(BaseModel):
    decision: str  # confirm_threat | false_positive | escalate | needs_review
    notes: str = ""


# ---------------- Metrics ----------------
class MetricsOverview(BaseModel):
    total_alerts: int
    threats: int
    false_positives: int
    open_alerts: int
    avg_confidence: float
    by_severity: dict[str, int]
    by_event_type: dict[str, int]
    fp_reduction_estimate_pct: float
