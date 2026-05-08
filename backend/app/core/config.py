"""Application configuration loaded from environment."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "SOC AI Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Mode: "mock" generates synthetic alerts; "splunk" pulls from Splunk
    DATA_MODE: str = "mock"

    # Auth
    JWT_SECRET: str = "change-me-in-production-please-please"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://soc:soc@db:5432/socai"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Splunk
    SPLUNK_HOST: str = "localhost"
    SPLUNK_PORT: int = 8089
    SPLUNK_USERNAME: str = "admin"
    SPLUNK_PASSWORD: str = "changeme"
    SPLUNK_SCHEME: str = "https"
    SPLUNK_INDEX: str = "main"
    SPLUNK_POLL_INTERVAL_SECONDS: int = 60
    SPLUNK_VERIFY_SSL: bool = False

    # ML
    ML_MODEL_PATH: str = "/app/ml/models/xgb_alert_classifier.joblib"
    ML_FEATURE_PIPELINE_PATH: str = "/app/ml/models/feature_pipeline.joblib"

    # Mock data generator
    MOCK_ALERT_INTERVAL_SECONDS: int = 30
    MOCK_ALERTS_PER_BATCH: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
