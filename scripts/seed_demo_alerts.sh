#!/usr/bin/env bash
# =====================================================================
# Push canned demo alerts directly into the backend ingest endpoint.
# Useful when you need a deterministic demo and don't want to wait for
# the poller. Run from your laptop while the backend is up.
# =====================================================================

set -euo pipefail

API="${API:-http://localhost:8000/api/v1}"

# 1) login
TOKEN=$(curl -fsS -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst","password":"analyst123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

post_alert () {
  curl -fsS -X POST "$API/alerts/ingest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$1" | python3 -m json.tool
}

echo "[+] Brute force"
post_alert '{
  "source_id": "demo-bf-001",
  "source": "demo",
  "title": "RDP brute force against Administrator",
  "description": "30 failed logons in 4 minutes from external IP",
  "severity": "high",
  "src_ip": "203.0.113.45",
  "dst_ip": "192.168.56.20",
  "user": "Administrator",
  "host": "WIN-VICTIM01",
  "event_type": "failed_login",
  "failed_login_count": 30
}'

echo "[+] PowerShell encoded payload"
post_alert '{
  "source_id": "demo-ps-001",
  "source": "demo",
  "title": "PowerShell encoded command on WIN-VICTIM01",
  "description": "Sysmon event 1: powershell.exe -nop -w hidden -enc <b64>",
  "severity": "critical",
  "src_ip": "192.168.56.20",
  "user": "jdoe",
  "host": "WIN-VICTIM01",
  "event_type": "powershell_execution",
  "process_name": "powershell.exe",
  "command_line": "powershell.exe -nop -w hidden -enc SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQA"
}'

echo "[+] Likely false positive — backup job"
post_alert '{
  "source_id": "demo-fp-001",
  "source": "demo",
  "title": "Scheduled backup process",
  "description": "Nightly backup job started by svc_backup",
  "severity": "low",
  "src_ip": "10.0.0.5",
  "user": "svc_backup",
  "host": "WIN-VICTIM01",
  "event_type": "process_create",
  "process_name": "backup.exe",
  "command_line": "backup.exe --schedule daily"
}'

echo "[+] Mimikatz credential dumping"
post_alert '{
  "source_id": "demo-mz-001",
  "source": "demo",
  "title": "Suspected credential dumping (mimikatz)",
  "description": "lsass access pattern + sekurlsa::logonpasswords",
  "severity": "critical",
  "src_ip": "192.168.56.20",
  "user": "admin",
  "host": "WIN-VICTIM01",
  "event_type": "process_create",
  "process_name": "mimikatz.exe",
  "command_line": "mimikatz.exe sekurlsa::logonpasswords"
}'

echo "[+] All demo alerts ingested. Open http://localhost:5173"
