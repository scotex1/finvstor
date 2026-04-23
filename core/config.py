"""
core/config.py — Environment configuration
All secrets loaded from .env file
"""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────
    APP_NAME:    str  = "FinVest Pro"
    DEBUG:       bool = False
    SECRET_KEY:  str  = "change-this-in-production-use-openssl-rand-hex-32"
    API_VERSION: str  = "v1"

    # ── CORS ───────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://yourdomain.com",       # ← Change this
        "https://www.yourdomain.com",   # ← Change this
    ]

    # ── Firebase ───────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "firebase/serviceAccountKey.json"
    FIREBASE_PROJECT_ID:       str = "your-firebase-project-id"  # ← Change

    # ── Database (Optional — for caching) ─────────────────
    DATABASE_URL: str = "sqlite:///./finvest.db"   # Dev default
    # DATABASE_URL = "postgresql://user:pass@host/dbname"  # Prod

    # ── Cashfree Payment Gateway ───────────────────────────
    CASHFREE_APP_ID:     str = "your-cashfree-app-id"      # ← Change
    CASHFREE_SECRET_KEY: str = "your-cashfree-secret-key"  # ← Change
    CASHFREE_BASE_URL:   str = "https://sandbox.cashfree.com/pg"  # sandbox
    # CASHFREE_BASE_URL = "https://api.cashfree.com/pg"  # production

    # ── Plan Pricing (in paise for Cashfree) ──────────────
    PLAN_PRICES: dict = {
        "basic":        49900,   # ₹499
        "pro":          99900,   # ₹999
        "elite":       199900,   # ₹1999
        "basic_yearly": 449900,  # ₹4499
        "pro_yearly":   899900,  # ₹8999
    }

    # ── Plan Durations (days) ─────────────────────────────
    PLAN_DURATIONS: dict = {
        "basic":        30,
        "pro":          30,
        "elite":        30,
        "basic_yearly": 365,
        "pro_yearly":   365,
    }

    # ── Stock / Market Data API ────────────────────────────
    MARKET_DATA_API_KEY: str = "your-market-data-api-key"  # ← Change
    # Options: Alpha Vantage, NSE API, Yahoo Finance, Groww API

    # ── AI (for AI engines) ───────────────────────────────
    OPENAI_API_KEY:    str = ""   # for GPT-based analysis
    ANTHROPIC_API_KEY: str = ""   # for Claude-based analysis

    # ── News API ───────────────────────────────────────────
    NEWS_API_KEY: str = "your-newsapi-key"  # newsapi.org

    # ── Redis (optional — for rate limiting / caching) ────
    REDIS_URL: str = ""   # "redis://localhost:6379"

    # ── Email (for notifications) ─────────────────────────
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
