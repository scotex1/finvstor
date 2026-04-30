"""
FinVest Pro — FastAPI Backend
main.py — App entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from core.config import settings
from firebase.firebase_config import initialize_firebase

from routes.auth_routes         import router as auth_router
from routes.user_routes         import router as user_router
from routes.investment_routes   import router as investment_router
from routes.subscription_routes import router as subscription_router
from routes.admin_routes        import router as admin_router

from middleware.auth_middleware         import AuthMiddleware
from middleware.subscription_middleware import SubscriptionMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("finvest")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 FinVest Pro starting...")
    initialize_firebase()
    logger.info("✅ Firebase ready | Storage: Firestore (cloud) | Cache: in-memory")
    yield
    logger.info("🛑 Shutting down...")


app = FastAPI(
    title="FinVest Pro API",
    version="1.0.0",
    docs_url="/docs"  if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(SubscriptionMiddleware)

app.include_router(auth_router,         prefix="/api/v1/auth",    tags=["Auth"])
app.include_router(user_router,         prefix="/api/v1/user",    tags=["User"])
app.include_router(investment_router,   prefix="/api/v1/engines", tags=["Engines"])
app.include_router(subscription_router, prefix="/api/v1/payment", tags=["Payments"])
app.include_router(admin_router,        prefix="/api/v1/admin",   tags=["Admin"])


@app.get("/health", tags=["Health"])
async def health():
    from database.models import cache_stats
    return {
        "status":  "ok",
        "version": "1.0.0",
        "storage": "Firestore",
        "cache":   cache_stats(),
    }

@app.get("/", tags=["Health"])
async def root():
    return {"message": "FinVest Pro API v1.0"}
