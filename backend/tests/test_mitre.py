"""Tests for MITRE rule-based mapping."""
from app.mitre.engine import get_mitre_engine


def test_brute_force_maps_to_t1110():
    eng = get_mitre_engine()
    hits = eng.map_alert({
        "title": "Multiple failed logins", "event_type": "failed_login",
        "failed_login_count": 25,
    })
    ids = {h.technique_id for h in hits}
    assert "T1110" in ids
    assert "T1110.001" in ids


def test_powershell_encoded_maps_to_t1059_001_and_t1027():
    eng = get_mitre_engine()
    hits = eng.map_alert({
        "title": "Suspicious ps", "event_type": "process_create",
        "process_name": "powershell.exe",
        "command_line": "powershell.exe -nop -w hidden -enc QUJD",
    })
    ids = {h.technique_id for h in hits}
    assert "T1059.001" in ids
    assert "T1027" in ids


def test_mimikatz_maps_to_t1003():
    eng = get_mitre_engine()
    hits = eng.map_alert({
        "title": "lsass dump",
        "command_line": "mimikatz.exe sekurlsa::logonpasswords",
    })
    assert any(h.technique_id == "T1003" for h in hits)


def test_benign_alert_no_hits():
    eng = get_mitre_engine()
    hits = eng.map_alert({
        "title": "user login", "event_type": "successful_login",
        "user": "alice", "is_off_hours": False,
    })
    assert hits == []
