"""DB initialization: create tables and seed default users."""
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import db_models  # noqa: F401  (registers tables)
from app.models.db_models import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                username="admin", email="admin@socai.local",
                hashed_password=hash_password("admin123"),
                role="admin",
            ))
        if not db.query(User).filter(User.username == "analyst").first():
            db.add(User(
                username="analyst", email="analyst@socai.local",
                hashed_password=hash_password("analyst123"),
                role="analyst",
            ))
        db.commit()
    finally:
        db.close()
