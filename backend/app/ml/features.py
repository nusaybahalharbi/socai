"""Feature engineering for the alert classifier.

Converts a normalized alert dict into a numeric feature vector.
Same function used for training (offline) and inference (online).
"""
from __future__ import annotations

from typing import Any
import re

import numpy as np
import pandas as pd

# Severity ordinal
SEVERITY_MAP = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

# Event-type one-hot vocabulary (kept small for MVP)
EVENT_TYPES = [
    "failed_login", "successful_login", "powershell_execution",
    "cmd_execution", "file_create", "network_connection",
    "process_create", "service_install", "registry_modification",
    "port_scan", "lateral_movement", "other",
]


def _is_internal(ip: str | None) -> int:
    if not ip:
        return 0
    return int(bool(re.match(r"^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|127\.)", ip)))


def _suspicious_cmd_score(cmd: str | None) -> float:
    if not cmd:
        return 0.0
    cmd = cmd.lower()
    flags = [
        "-enc", "frombase64string", "iex", "invoke-expression",
        "downloadstring", "downloadfile", "-nop", "-w hidden",
        "bypass", "mimikatz", "lsass", "procdump", "vssadmin delete",
    ]
    return sum(1 for f in flags if f in cmd) / max(1, len(flags))


def _is_admin_user(user: str | None) -> int:
    if not user:
        return 0
    return int(any(k in user.lower() for k in ["admin", "root", "svc", "service"]))


def alert_to_features(alert: dict[str, Any]) -> dict[str, float]:
    """Return a flat dict of feature_name -> float for one alert."""
    feats: dict[str, float] = {}

    feats["severity_ord"] = float(SEVERITY_MAP.get((alert.get("severity") or "medium").lower(), 2))
    feats["failed_login_count"] = float(alert.get("failed_login_count") or 0)
    feats["hour_of_day"] = float(alert.get("hour_of_day") or 0)
    feats["is_off_hours"] = float(int(bool(alert.get("is_off_hours"))))
    feats["src_internal"] = float(_is_internal(alert.get("src_ip")))
    feats["dst_internal"] = float(_is_internal(alert.get("dst_ip")))
    feats["is_admin_user"] = float(_is_admin_user(alert.get("user")))
    feats["cmd_suspicious_score"] = float(_suspicious_cmd_score(alert.get("command_line")))
    feats["cmd_length"] = float(len(alert.get("command_line") or ""))
    feats["title_length"] = float(len(alert.get("title") or ""))

    et = (alert.get("event_type") or "other").lower()
    if et not in EVENT_TYPES:
        et = "other"
    for name in EVENT_TYPES:
        feats[f"et__{name}"] = 1.0 if et == name else 0.0

    return feats


FEATURE_NAMES: list[str] = list(alert_to_features({}).keys())


def alerts_to_dataframe(alerts: list[dict[str, Any]]) -> pd.DataFrame:
    rows = [alert_to_features(a) for a in alerts]
    df = pd.DataFrame(rows, columns=FEATURE_NAMES)
    return df


def alert_to_vector(alert: dict[str, Any]) -> np.ndarray:
    feats = alert_to_features(alert)
    return np.array([feats[n] for n in FEATURE_NAMES], dtype=np.float32).reshape(1, -1)
