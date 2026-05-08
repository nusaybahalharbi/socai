# Architecture

```
                       ┌─────────────────────────┐
                       │      Kali Linux         │
                       │  (attacker — hydra,     │
                       │   nmap, mimikatz, etc.) │
                       └────────────┬────────────┘
                                    │ attacks
                                    ▼
        ┌──────────────────────────────────────────────────────┐
        │                  Windows VM (victim)                 │
        │   ┌─────────────┐  ┌──────────────────────────────┐ │
        │   │   Sysmon    │  │  Splunk Universal Forwarder  │ │
        │   └─────┬───────┘  └──────────────┬───────────────┘ │
        └─────────┼─────────────────────────┼─────────────────┘
                  └─── Windows Security ────┘
                                │
                                ▼
                  ┌────────────────────────────┐
                  │   Ubuntu VM — Splunk       │
                  │       Enterprise           │
                  └─────────────┬──────────────┘
                                │ REST (splunk-sdk)
                                ▼
        ┌──────────────────────────────────────────────────────┐
        │          Main Laptop — SOC AI Platform               │
        │                                                      │
        │   FastAPI ──► Ingestion ──► Classifier (XGBoost)     │
        │      │            │              │                   │
        │      │            ▼              ▼                   │
        │      │       MITRE Engine   SHAP Explainer           │
        │      │            │              │                   │
        │      ▼            ▼              ▼                   │
        │   PostgreSQL  ◄── persisted alerts + predictions     │
        │      ▲                                               │
        │      │ REST                                          │
        │      ▼                                               │
        │   React + Tailwind dashboard (Vite)                  │
        └──────────────────────────────────────────────────────┘
```

## Component responsibilities

| Layer       | Component                | Responsibility                                             |
|-------------|--------------------------|------------------------------------------------------------|
| Lab         | Kali                     | Generate adversary behaviour                               |
| Lab         | Windows + Sysmon + UF    | Produce + ship events                                      |
| Lab         | Ubuntu + Splunk          | SIEM of record                                             |
| Backend     | `connectors.splunk`      | Pull events via SDK, normalize                             |
| Backend     | `connectors.mock`        | Synthetic events when DATA_MODE=mock                       |
| Backend     | `services.scheduler`     | Periodic poll job                                          |
| Backend     | `services.ingestion`     | Persist → classify → MITRE-map → recommend                 |
| Backend     | `ml.inference`           | XGBoost + SHAP, heuristic fallback                         |
| Backend     | `mitre.engine`           | Rule-based ATT&CK mapper                                   |
| Backend     | `api.*`                  | REST endpoints (auth, alerts, metrics, MITRE)              |
| DB          | PostgreSQL               | alerts, predictions, mitre_mappings, feedback, users, audit|
| Frontend    | React + Tailwind         | Dashboard, queue, detail, MITRE heatmap, metrics           |

## Data flow (one alert)

1. Splunk emits an event matching the saved search.
2. Scheduler (every `SPLUNK_POLL_INTERVAL_SECONDS`) calls `SplunkConnector.fetch_alerts`.
3. Connector normalizes Splunk fields → canonical dict.
4. `ingest_one` dedupes by `source_id`, persists `Alert`.
5. `Classifier.predict` returns `(label, confidence, SHAP)`.
6. `MitreEngine.map_alert` returns ATT&CK hits.
7. `build_recommendation` writes analyst guidance.
8. `Prediction` + `MitreMapping` rows persisted.
9. Dashboard polls `/alerts`, renders triage queue.
10. Analyst clicks an alert → `/alerts/{id}` shows full enrichment, SHAP bars, MITRE cards, action buttons.
11. Feedback (`confirm_threat` / `false_positive` / `escalate` / `needs_review`) is stored for retraining.
