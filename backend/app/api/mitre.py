"""Read-only MITRE endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.mitre.engine import get_mitre_engine
from app.models.db_models import MitreMapping, User

router = APIRouter(prefix="/mitre", tags=["mitre"])


@router.get("/techniques")
def list_techniques(user: User = Depends(get_current_user)):
    """Return the loaded MITRE technique catalog used by the engine."""
    engine = get_mitre_engine()
    return list(engine.catalog.values())


@router.get("/heatmap")
def heatmap(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Aggregate technique counts across all alerts (for an ATT&CK navigator-style view)."""
    rows = db.query(
        MitreMapping.technique_id,
        MitreMapping.technique_name,
        MitreMapping.tactic,
    ).all()
    counts: dict[str, dict] = {}
    for tid, tname, tactic in rows:
        if tid not in counts:
            counts[tid] = {"technique_id": tid, "technique_name": tname, "tactic": tactic, "count": 0}
        counts[tid]["count"] += 1
    return sorted(counts.values(), key=lambda x: -x["count"])
