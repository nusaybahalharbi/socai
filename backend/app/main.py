"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, auth, mitre
from app.core.config import settings
from app.db.init_db import init_db
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("soc-ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Booting %s in %s mode (data_mode=%s)", settings.APP_NAME, settings.APP_ENV, settings.DATA_MODE)
    init_db()
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="AI-powered SOC Intelligence Platform — alert triage, MITRE ATT&CK enrichment, analyst recommendations.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "mode": settings.DATA_MODE}


# Mount routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.metrics_router, prefix=settings.API_V1_PREFIX)
app.include_router(mitre.router, prefix=settings.API_V1_PREFIX)
