"""Rule-based MITRE ATT&CK mapping engine.

Hybrid approach: regex/keyword rules over normalized alert fields + numeric thresholds.
Each rule emits one or more (technique_id, confidence, rationale) tuples.
The catalog (techniques.json) provides tactic and human-readable name for each id.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).parent / "techniques.json"


@dataclass
class MitreHit:
    technique_id: str
    technique_name: str
    tactic: str
    confidence: float
    rationale: str


class MitreEngine:
    def __init__(self, catalog_path: Path = CATALOG_PATH):
        with open(catalog_path) as f:
            data = json.load(f)
        self.catalog: dict[str, dict[str, str]] = {
            t["id"]: t for t in data["techniques"]
        }

    def _resolve(self, technique_id: str, confidence: float, rationale: str) -> MitreHit | None:
        meta = self.catalog.get(technique_id)
        if not meta:
            return None
        return MitreHit(
            technique_id=technique_id,
            technique_name=meta["name"],
            tactic=meta["tactic"],
            confidence=confidence,
            rationale=rationale,
        )

    def map_alert(self, alert: dict[str, Any]) -> list[MitreHit]:
        """Inspect a normalized alert dict and return a list of MITRE hits."""
        hits: list[MitreHit] = []
        event_type = (alert.get("event_type") or "").lower()
        title = (alert.get("title") or "").lower()
        desc = (alert.get("description") or "").lower()
        cmd = (alert.get("command_line") or "").lower()
        proc = (alert.get("process_name") or "").lower()
        failed = int(alert.get("failed_login_count") or 0)
        text = f"{title} {desc} {cmd} {proc} {event_type}"

        # --- Brute force / credential access ---
        if failed >= 5 or "brute" in text or "failed login" in text or "logon failure" in text:
            base = 0.95 if failed >= 20 else 0.8 if failed >= 10 else 0.65
            rationale = f"{failed} failed logins detected" if failed else "Failed authentication pattern in alert text"
            hits.append(self._resolve("T1110", base, rationale))
            if failed >= 5:
                hits.append(self._resolve(
                    "T1110.001", min(0.9, base + 0.05),
                    "Repeated failures against single account suggest password guessing"
                ))

        # --- PowerShell execution ---
        if "powershell" in text or "powershell.exe" in proc:
            conf = 0.9 if any(k in cmd for k in ["-enc", "iex", "downloadstring", "bypass", "hidden"]) else 0.7
            rationale = "Suspicious PowerShell flags detected" if conf >= 0.9 else "PowerShell execution observed"
            hits.append(self._resolve("T1059.001", conf, rationale))
            hits.append(self._resolve("T1059", 0.6, "Scripting interpreter usage"))

        # --- cmd.exe ---
        if "cmd.exe" in proc or re.search(r"\bcmd\.exe\b", cmd):
            hits.append(self._resolve("T1059.003", 0.6, "Windows command shell invoked"))

        # --- Obfuscation indicators ---
        if "-enc" in cmd or "base64" in cmd or "frombase64string" in cmd:
            hits.append(self._resolve("T1027", 0.85, "Encoded/obfuscated command line content"))

        # --- Credential dumping signals ---
        if any(tool in text for tool in ["mimikatz", "lsass", "sekurlsa", "procdump"]):
            hits.append(self._resolve("T1003", 0.9, "Indicators of credential dumping tooling"))

        # --- Discovery / scanning ---
        if any(tool in text for tool in ["nmap", "port scan", "masscan", "rustscan"]):
            hits.append(self._resolve("T1046", 0.8, "Network scanning behavior detected"))

        # --- Lateral movement ---
        if any(k in text for k in ["psexec", "wmiexec", "rdp brute", "smb session"]):
            hits.append(self._resolve("T1021", 0.75, "Remote service access pattern"))

        # --- Suspicious login: valid account abuse / off hours ---
        if alert.get("is_off_hours") and event_type in {"successful_login", "logon_success"}:
            hits.append(self._resolve("T1078", 0.6, "Successful login during off-hours"))

        # --- Ransomware / impact ---
        if any(k in text for k in ["ransom", "encrypted", ".lock", "vssadmin delete"]):
            hits.append(self._resolve("T1486", 0.9, "Ransomware behavior indicators"))

        # --- Web exploit ---
        if any(k in text for k in ["sql injection", "rce", "log4j", "/etc/passwd", "exploit"]):
            hits.append(self._resolve("T1190", 0.7, "Public-facing app exploit indicators"))

        # de-dupe by technique_id keeping highest confidence
        best: dict[str, MitreHit] = {}
        for h in hits:
            if h is None:
                continue
            if h.technique_id not in best or h.confidence > best[h.technique_id].confidence:
                best[h.technique_id] = h
        return sorted(best.values(), key=lambda x: -x.confidence)


# module-level singleton
_engine: MitreEngine | None = None


def get_mitre_engine() -> MitreEngine:
    global _engine
    if _engine is None:
        _engine = MitreEngine()
    return _engine
