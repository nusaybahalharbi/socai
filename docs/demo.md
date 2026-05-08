# August Demo Script

## Pre-flight (do this 30 min before)

1. `docker compose up --build -d` on the laptop. Wait for `socai-backend` health.
2. Open `http://localhost:5173`. Log in as `analyst / analyst123`.
3. Confirm the Overview page is populating with mock alerts (mock mode is the default).
4. If presenting full lab flow:
   - Boot the **Ubuntu/Splunk VM** and confirm Splunk is reachable on `:8089`.
   - Boot the **Windows VM**. Sysmon running, UF forwarding to Splunk (verify with `index=main earliest=-5m | stats count by sourcetype`).
   - Boot **Kali**. Confirm reachability to Windows IP.
5. If switching to live mode: edit `.env` → `DATA_MODE=splunk` and Splunk creds, then `docker compose restart backend`.

## The 7-minute demo

### Minute 0–1: The problem (slide)
> "An NCA-aligned SOC running Splunk receives ~3,000 alerts/day. A Level-1 analyst can triage maybe 80. The rest are noise — but the 12 real threats hide inside it. Our platform sits between Splunk and the analyst and does the first 80% of triage automatically, with explainability."

### Minute 1–2: Live attack from Kali
- On Kali: `bash scripts/kali_bruteforce_demo.sh` (set `TARGET_IP` to the Windows VM).
- Switch to Splunk: search `index=main EventCode=4625 earliest=-2m` — show events arriving.

### Minute 2–4: AI ingestion + classification
- Switch to the SOC AI dashboard → Overview.
- Within ~1 minute the new alerts appear. Severity pill, AI label, confidence bar visible in the queue.
- Click the brute-force alert. Show:
  - Top features driving the classification (SHAP).
  - MITRE mapping: `T1110 Brute Force` → tactic `Credential Access`, plus `T1110.001`.
  - Concrete recommendation: lock account, block source IP.

### Minute 4–5: False positive triage
- Back to the queue. Filter by `AI Label = false positive`.
- Click one (e.g. backup job). Show why the model demoted it (low cmd-suspicious score, business hours, internal user).
- Hit **Mark False Positive** → status flips to `closed`. "That's six minutes of analyst time saved per alert."

### Minute 5–6: SOC Metrics
- Open `Metrics`. Show:
  - Auto-triage rate (% of FPs the AI handled).
  - Estimated analyst hours saved.
  - Open alerts.
- "On a real Splunk feed at 3,000 alerts/day with 70% FP rate, that's ~210 analyst-hours/month back."

### Minute 6–7: MITRE coverage view
- Open `MITRE ATT&CK`. Heatmap by tactic. Walk through what's lighting up.
- Close: "This is the layer your Level-1 analysts have been asking for. Splunk stays. SOAR stays. We make both more effective."

## Recovery moves if something breaks

| Symptom                              | Fix                                                                                      |
|--------------------------------------|------------------------------------------------------------------------------------------|
| Backend says model unavailable       | Heuristic fallback still classifies; rerun `docker compose exec backend python -m app.ml.train`. |
| No alerts appearing in mock mode     | `docker compose logs backend | grep poll` — restart backend if no poll lines.            |
| Splunk connector errors              | Quick fallback: `bash scripts/seed_demo_alerts.sh` — pushes 4 deterministic demo alerts. |
| Frontend shows 401                   | Token expired — re-login.                                                                 |

## Talking points the audience will ask about

- **"Is this another SIEM?"** No. Splunk stays the system of record. We're the analyst-augmentation layer on top.
- **"Why XGBoost?"** Tabular features, fast training, native SHAP support, runs on CPU.
- **"How do you handle drift?"** Analyst feedback is stored (`analyst_feedback` table). Retrain weekly on the labeled feedback set.
- **"NCA / regulatory fit?"** All decisions auditable (`audit_logs`), explainability is per-alert, deployment is on-prem-friendly (Docker).
