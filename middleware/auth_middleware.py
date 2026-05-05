"""
middleware/auth_middleware.py — Firebase token verification
CORS is handled by FastAPI CORSMiddleware BEFORE this runs
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from firebase_admin import auth as firebase_auth
import logging

logger = logging.getLogger(__name__)

# Routes that do NOT require auth token
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/sync",
    "/api/v1/payment/webhook",
}

PUBLIC_PREFIXES = ("/docs", "/redoc", "/openapi")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path   = request.url.path
        method = request.method

        # ── Always pass through OPTIONS (CORS preflight) ──
        # CORSMiddleware handles it — but belt + suspenders
        if method == "OPTIONS":
            return await call_next(request)

        # ── Public routes ─────────────────────────────────
        if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        # ── Require Bearer token ──────────────────────────
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header missing. Expected: Bearer <token>"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token is empty."},
            )

        # ── Verify with Firebase ──────────────────────────
        try:
            decoded = firebase_auth.verify_id_token(token, check_revoked=True)
            request.state.uid        = decoded["uid"]
            request.state.email      = decoded.get("email", "")
            request.state.token_data = decoded
        except firebase_auth.RevokedIdTokenError:
            return JSONResponse(status_code=401, content={"detail": "Token revoked. Please sign in again."})
        except firebase_auth.ExpiredIdTokenError:
            return JSONResponse(status_code=401, content={"detail": "Token expired. Please sign in again."})
        except firebase_auth.InvalidIdTokenError as e:
            return JSONResponse(status_code=401, content={"detail": f"Invalid token: {str(e)}"})
        except Exception as e:
            logger.warning(f"Token verification error: {e}")
            return JSONResponse(status_code=401, content={"detail": "Authentication failed."})

        return await call_next(request)

