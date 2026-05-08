"""Inference service: classify an alert + produce SHAP-based explanation.

Loads the trained model bundle once and reuses it for every prediction.
If the model file does not yet exist, falls back to a heuristic so the API
still returns predictions while training is pending.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.core.config import settings
from app.ml.features import FEATURE_NAMES, alert_to_features, alert_to_vector


class Classifier:
    def __init__(self):
        self.bundle: dict | None = None
        self.shap_explainer = None
        self._try_load()

    def _try_load(self) -> None:
        path = Path(settings.ML_MODEL_PATH)
        if path.exists():
            try:
                self.bundle = joblib.load(path)
                # lazy SHAP explainer
                try:
                    import shap  # noqa: WPS433
                    self.shap_explainer = shap.TreeExplainer(self.bundle["model"])
                except Exception as e:  # pragma: no cover
                    print(f"[ml] SHAP unavailable: {e}")
            except Exception as e:  # pragma: no cover
                print(f"[ml] Failed to load model bundle: {e}")
                self.bundle = None

    def reload(self) -> None:
        self.bundle = None
        self.shap_explainer = None
        self._try_load()

    @property
    def is_ready(self) -> bool:
        return self.bundle is not None

    # ---------- Heuristic fallback ----------
    @staticmethod
    def _heuristic(alert: dict[str, Any]) -> tuple[str, float, dict[str, Any]]:
        score = 0.0
        reasons: list[tuple[str, float]] = []
        if (alert.get("failed_login_count") or 0) >= 5:
            v = min(0.4, 0.02 * alert["failed_login_count"])
            score += v; reasons.append(("failed_login_count", v))
        cmd = (alert.get("command_line") or "").lower()
        if any(k in cmd for k in ["-enc", "iex", "downloadstring", "mimikatz", "vssadmin delete"]):
            score += 0.4; reasons.append(("cmd_suspicious_score", 0.4))
        if alert.get("is_off_hours"):
            score += 0.1; reasons.append(("is_off_hours", 0.1))
        sev = (alert.get("severity") or "medium").lower()
        if sev in ("high", "critical"):
            score += 0.2; reasons.append(("severity_ord", 0.2))
        score = min(0.99, score)
        label = "threat" if score >= 0.5 else "false_positive"
        explanation = {
            "method": "heuristic",
            "top_features": [{"feature": k, "impact": v} for k, v in sorted(reasons, key=lambda x: -x[1])[:5]],
        }
        return label, score, explanation

    # ---------- ML path ----------
    def predict(self, alert: dict[str, Any]) -> tuple[str, float, dict[str, Any]]:
        if not self.is_ready:
            return self._heuristic(alert)
        model = self.bundle["model"]
        label_map = self.bundle["label_map"]
        x = alert_to_vector(alert)
        proba = model.predict_proba(x)[0]
        idx = int(np.argmax(proba))
        label = label_map[idx]
        confidence = float(proba[idx])

        explanation: dict[str, Any] = {"method": "shap", "top_features": []}
        try:
            if self.shap_explainer is not None:
                shap_values = self.shap_explainer.shap_values(x)
                # XGBoost binary -> 2D array (1, n_features)
                vals = np.array(shap_values).reshape(-1)
                feats = alert_to_features(alert)
                ranked = sorted(
                    zip(FEATURE_NAMES, vals),
                    key=lambda kv: -abs(float(kv[1])),
                )[:6]
                explanation["top_features"] = [
                    {
                        "feature": name,
                        "value": float(feats.get(name, 0.0)),
                        "impact": float(impact),
                        "direction": "increases_threat" if impact > 0 else "decreases_threat",
                    }
                    for name, impact in ranked
                ]
        except Exception as e:  # pragma: no cover
            explanation["error"] = str(e)

        return label, confidence, explanation


_classifier: Classifier | None = None


def get_classifier() -> Classifier:
    global _classifier
    if _classifier is None:
        _classifier = Classifier()
    return _classifier


# ---------- Recommendation generator ----------
def build_recommendation(alert: dict[str, Any], label: str, mitre_hits: list) -> str:
    """Generate analyst-friendly SOC recommendation text."""
    if label == "false_positive":
        return (
            "Likely benign. Suggested action: close as false positive after a "
            "quick verification of the source host and user. Add to tuning "
            "candidates if this pattern repeats."
        )
    actions: list[str] = []
    techniques = {h.technique_id for h in mitre_hits}
    if "T1110" in techniques or "T1110.001" in techniques:
        actions.append(
            f"Lock or force-reset account '{alert.get('user') or 'affected user'}' "
            f"and block source IP {alert.get('src_ip') or '<unknown>'} at the firewall."
        )
    if "T1059.001" in techniques or "T1059" in techniques:
        actions.append(
            f"Isolate host '{alert.get('host') or 'endpoint'}' and capture the full "
            "PowerShell command line + parent process tree for IR."
        )
    if "T1003" in techniques:
        actions.append("Treat as in-progress credential theft: rotate domain admin credentials and start IR playbook.")
    if "T1486" in techniques:
        actions.append("Suspected ransomware: isolate host immediately and engage IR.")
    if not actions:
        actions.append(
            f"Investigate host '{alert.get('host') or '<unknown>'}' and user "
            f"'{alert.get('user') or '<unknown>'}'. Pivot on src_ip "
            f"{alert.get('src_ip') or '<unknown>'} for related activity in the last 24h."
        )
    return " ".join(f"{i+1}) {a}" for i, a in enumerate(actions))
