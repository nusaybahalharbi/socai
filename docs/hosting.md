# Hosting

## Option A: Local-only (laptop, fastest)
```bash
docker compose up --build
```
- Backend at `http://localhost:8000` (docs at `/docs`)
- Frontend at `http://localhost:5173`
- Postgres at `localhost:5432`

## Option B: Vercel (frontend) + Render (backend) + Neon (Postgres)

### 1. Database — Neon
1. Create a free Neon project. Copy the connection string.
2. Convert to SQLAlchemy form: replace `postgres://` with `postgresql+psycopg2://` and append `?sslmode=require`.

### 2. Backend — Render
1. Create a new **Web Service** pointing at the repo, root `backend/`.
2. Runtime: Docker. Render builds the `backend/Dockerfile` automatically.
3. Set environment variables on Render:
   ```
   DATABASE_URL=postgresql+psycopg2://...neon...
   JWT_SECRET=<long random string>
   DATA_MODE=mock              # or splunk
   CORS_ORIGINS=https://your-app.vercel.app
   ```
4. (If `DATA_MODE=splunk`) add `SPLUNK_*` variables and ensure Splunk is reachable from Render. For private Splunk, set up a tunnel or VPN — most teams keep DATA_MODE=mock for hosted demos and run live Splunk on-prem.

### 3. Frontend — Vercel
1. Import the repo, set root to `frontend/`.
2. Build command: `npm run build`. Output: `dist`.
3. Environment variable:
   ```
   VITE_API_BASE_URL=https://<your-render-service>.onrender.com/api/v1
   ```
4. Deploy.

### 4. Smoke test
- Open the Vercel URL.
- Login `analyst / analyst123` (auto-seeded on first boot).
- Mock alerts populate within 30s.

## Option C: Railway
Same shape as Render. Add a Postgres plugin, point the backend service at `backend/Dockerfile`, set the same env vars.

## Production hardening checklist (post-MVP, not blocking demo)
- Replace seeded users; require password change on first login.
- Move JWT secret to a secrets manager (Render/Railway provide this).
- Enable SSL verification on Splunk (`SPLUNK_VERIFY_SSL=true`) once your Splunk has a real cert.
- Run `alembic` migrations instead of `Base.metadata.create_all` (scaffold present, schema lives in `app/models/db_models.py`).
- Pin Postgres backups (Neon does this automatically on paid tier).
- Add a reverse proxy with rate limiting in front of the backend.
