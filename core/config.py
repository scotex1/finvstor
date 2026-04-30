"""
core/config.py — Environment configuration
"""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
import json


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────
    APP_NAME:    str  = "FinVest Pro"
    DEBUG:       bool = False
    SECRET_KEY:  str  = "change-this-in-production"

    # ── CORS ──────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]

    # ── Firebase ──────────────────────────────────────────
    # Option A: JSON string (recommended for Render)
    FIREBASE_CREDENTIALS_JSON: str = ""
    # Option B: file path (local dev only)
    FIREBASE_CREDENTIALS_PATH: str = "firebase/serviceAccountKey.json"
    FIREBASE_PROJECT_ID:       str = "your-firebase-project-id"

    # ── NO SQLite on Render — Firestore is primary DB ─────
    # SQLite only used locally for market data caching
    # On Render, in-memory cache is used instead
    USE_SQLITE_CACHE: bool = False   # Set True only for local dev

    # ── Cashfree ──────────────────────────────────────────
    CASHFREE_APP_ID:     str = ""
    CASHFREE_SECRET_KEY: str = ""
    CASHFREE_BASE_URL:   str = "https://sandbox.cashfree.com/pg"

    # ── Plan Pricing (paise) ──────────────────────────────
    PLAN_PRICES: dict = {
        "basic":        49900,
        "pro":          99900,
        "elite":       199900,
        "basic_yearly": 449900,
        "pro_yearly":   899900,
    }

    PLAN_DURATIONS: dict = {
        "basic":        30,
        "pro":          30,
        "elite":        30,
        "basic_yearly": 365,
        "pro_yearly":   365,
    }

    # ── APIs ──────────────────────────────────────────────
    NEWS_API_KEY:      str = ""
    ANTHROPIC_API_KEY: str = ""

    # ── Email (optional) ──────────────────────────────────
    SMTP_HOST:     str = "smtp.gmail.com"
    SMTP_PORT:     int = 587
    SMTP_USER:     str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL:    str = "noreply@finvestpro.in"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

