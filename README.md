# SOC AI Platform

> **AI-powered analyst-augmentation layer that sits between Splunk and your SOC.**
> Reduces alert fatigue. Triages threats vs. false positives. Maps to MITRE ATT&CK. Explains every decision.

This is **not** another SIEM. It's not a SOAR. It's not a chatbot. It's the layer your Level-1 analysts have been asking for: take 3,000 noisy Splunk alerts a day, hand back 200 prioritized ones with an AI label, a confidence score, MITRE context, and a concrete recommendation per alert.

---

## What's in the box

- **FastAPI backend** with JWT auth, RBAC, ingestion pipeline, scheduled polling.
- **PostgreSQL** schema — alerts, predictions, MITRE mappings, analyst feedback, users, audit logs.
- **XGBoost classifier** with **SHAP explanations**, trained on a synthetic SOC dataset on first build, with a heuristic fallback so the API never returns a blank prediction.
- **Rule-based MITRE ATT&CK engine** covering T1110, T1059, T1003, T1027, T1486, T1078, T1046, T1021, T1190, and more.
- **Splunk SDK connector** + **mock connector** behind the same interface, switchable via one env var (`DATA_MODE`).
- **React + Vite + Tailwind** dashboard — login, overview with charts, filterable alert queue, alert detail with SHAP feature-impact bars + analyst action buttons + MITRE cards, ATT&CK tactic heatmap, SOC metrics.
- **Docker Compose** orchestration for the whole stack — `docker compose up` and you're live.
- **Demo scripts** — Kali brute-force trigger, deterministic demo-alert seeder, sample SPL.

---

## Quick start (local, 5 minutes)

```bash
git clone <your-repo-url> soc-ai-platform
cd soc-ai-platform
cp .env.example .env             # default DATA_MODE=mock works out of the box
docker compose up --build
```

Then open:
- **Dashboard**: http://localhost:5173 — login `analyst / analyst123`
- **API docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

Mock alerts start flowing in ~30s. Click any alert to see classification, SHAP explanation, MITRE mapping, and recommendation.

---

## Lab architecture (for the live attack demo)

```
Kali (attacker) ──▶ Windows VM (Sysmon + UF) ──▶ Ubuntu VM (Splunk) ──▶ SOC AI Platform (laptop)
```

See `docs/architecture.md` for the full picture and `docs/demo.md` for the 7-minute demo script.

### Switching from mock to live Splunk

Edit `.env`:
```
DATA_MODE=splunk
SPLUNK_HOST=192.168.56.10        # your Ubuntu VM IP
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=<your-password>
SPLUNK_INDEX=main
```
Then `docker compose restart backend`. The poller picks up live events on the next interval.

---

## Project layout

```
soc-ai-platform/
├── backend/                        FastAPI app
│   ├── app/
│   │   ├── api/                    auth, alerts, mitre, deps
│   │   ├── core/                   config, JWT/password helpers
│   │   ├── connectors/             splunk_connector.py, mock_connector.py
│   │   ├── db/                     SQLAlchemy session + init_db (seeds users)
│   │   ├── ml/                     features, synthetic data, train.py, inference.py (SHAP)
│   │   ├── mitre/                  techniques.json catalog + rule engine
│   │   ├── models/                 ORM models
│   │   ├── schemas/                Pydantic I/O
│   │   ├── services/               ingestion + APScheduler poller
│   │   └── main.py                 FastAPI entrypoint
│   ├── tests/                      pytest suite
│   ├── requirements.txt
│   └── Dockerfile                  trains model at build time
├── frontend/                       React + Vite + Tailwind
│   ├── src/
│   │   ├── components/             Layout, Pills (severity/label/confidence)
│   │   ├── hooks/useAuth.js
│   │   ├── lib/api.js              axios client
│   │   └── pages/                  Login, Overview, Alerts, AlertDetail, Mitre, Metrics, Settings
│   ├── nginx.conf                  reverse-proxies /api → backend
│   └── Dockerfile
├── scripts/
│   ├── kali_bruteforce_demo.sh
│   ├── seed_demo_alerts.sh
│   └── splunk_savedsearch.spl
├── docs/
│   ├── architecture.md
│   ├── demo.md
│   └── hosting.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API

Authoritative reference at `http://localhost:8000/docs`. Highlights:

| Method | Path                              | Purpose                                      |
|--------|-----------------------------------|----------------------------------------------|
| POST   | `/api/v1/auth/login`              | Get a JWT                                    |
| GET    | `/api/v1/auth/me`                 | Current user                                 |
| GET    | `/api/v1/alerts`                  | Filterable alert queue (`status`, `label`, `severity`, `min_confidence`) |
| GET    | `/api/v1/alerts/{id}`             | Alert detail with prediction + MITRE         |
| POST   | `/api/v1/alerts/ingest`           | Ingest a single alert (used by Splunk webhook or demo seeder) |
| POST   | `/api/v1/alerts/{id}/feedback`    | Analyst decision: confirm_threat / false_positive / escalate / needs_review |
| GET    | `/api/v1/metrics/overview`        | KPIs over a time window                      |
| GET    | `/api/v1/mitre/techniques`        | Full technique catalog                       |
| GET    | `/api/v1/mitre/heatmap`           | Aggregate technique counts                   |

---

## ML pipeline

1. **Synthetic dataset** (`app/ml/synthetic.py`) — 4,000 labeled alerts spanning brute force, encoded PowerShell, mimikatz, ransomware, port scans, off-hours admin logins, plus benign legitimate logins, dev PowerShell sessions, backup jobs, AV scans.
2. **Feature engineering** (`app/ml/features.py`) — severity ordinal, failed-login count, hour-of-day, off-hours flag, internal-IP flags, admin-user flag, suspicious-cmd score, command length, plus one-hot event types.
3. **Training** (`app/ml/train.py`) — XGBoost binary classifier, prints precision/recall/F1, dumps a model bundle to `ml/models/xgb_alert_classifier.joblib`. Runs at Docker build time.
4. **Inference** (`app/ml/inference.py`) — loads bundle once, predicts per alert, computes SHAP TreeExplainer values, returns top-6 features with direction (`increases_threat` / `decreases_threat`). If the model file is missing, a transparent heuristic returns the same shape.

Retraining: collect analyst feedback rows, label, append to the training set, rerun `python -m app.ml.train`, restart the backend (or call a future `/admin/reload-model` endpoint).

---

## MITRE ATT&CK engine

Hybrid rules over the normalized alert (`app/mitre/engine.py`). Examples:
- `failed_login_count >= 5` → **T1110 Brute Force** (Credential Access).
- `command_line` contains `-enc` / `IEX` / `DownloadString` → **T1059.001 PowerShell** + **T1027 Obfuscation**.
- `mimikatz` / `lsass` / `sekurlsa` → **T1003 OS Credential Dumping**.
- `psexec` / `wmiexec` → **T1021 Remote Services**.
- Off-hours successful login → **T1078 Valid Accounts**.

The engine de-duplicates by technique ID, keeping the highest-confidence match.

---

## Tests

```bash
docker compose exec backend pytest -q
```

Covers the MITRE engine (positive + negative cases) and ML feature/heuristic paths. Extend by dropping new tests in `backend/tests/`.

---

## Deployment

See `docs/hosting.md` for Vercel + Render + Neon and Railway recipes. Short version:
- **Frontend** → Vercel (`frontend/` as root, `VITE_API_BASE_URL` to your backend URL).
- **Backend** → Render or Railway as a Docker service.
- **Database** → Neon Postgres free tier; use the `postgresql+psycopg2://...?sslmode=require` form in `DATABASE_URL`.

---

## Roadmap (post-MVP)

- Alembic migrations replacing `create_all`.
- Online retraining trigger from accumulated analyst feedback.
- ATT&CK Navigator JSON export from the heatmap view.
- Real-time websocket push of new alerts to the dashboard.
- Optional LLM-narrated explanation block alongside SHAP (per-alert investigative summary).
- VirusTotal / AbuseIPDB enrichment in the ingestion pipeline.

---

## License

MIT. Use it, fork it, ship it.
