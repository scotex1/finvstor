from pydantic_settings import BaseSettings
from typing import List, Dict
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────
    APP_NAME: str = "FinVest Pro"
    DEBUG: bool = false 
    SECRET_KEY: str = "change-this-in-production"

    # ── CORS ──────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5500",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:3000",
        "https://scotex1.github.io",
    ]

    ALLOWED_ORIGIN_REGEX: str = r"https://.*\.github\.io"

    # ── Firebase ──────────────────────────────────────────
    FIREBASE_CREDENTIALS_JSON: str = ""
    FIREBASE_CREDENTIALS_PATH: str = "firebase/serviceAccountKey.json"
    FIREBASE_PROJECT_ID: str = "your-firebase-project-id"

    # ── Cache ─────────────────────────────────────────────
    USE_SQLITE_CACHE: bool = False

    # ── Cashfree ──────────────────────────────────────────
    CASHFREE_APP_ID: str = ""
    CASHFREE_SECRET_KEY: str = ""
    CASHFREE_BASE_URL: str = "https://sandbox.cashfree.com/pg"

    # ── Plan Pricing (paise) ──────────────────────────────
    PLAN_PRICES: Dict[str, int] = {
        "basic": 49900,
        "pro": 99900,
        "elite": 199900,
        "basic_yearly": 449900,
        "pro_yearly": 899900,
    }

    PLAN_DURATIONS: Dict[str, int] = {
        "basic": 30,
        "pro": 30,
        "elite": 30,
        "basic_yearly": 365,
        "pro_yearly": 365,
    }

    # ── APIs ──────────────────────────────────────────────
    NEWS_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""

    # ── Email ─────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@finvestpro.in"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()





