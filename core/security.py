"""
core/security.py — Security utilities
Firebase token verification + JWT helpers
"""

from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from firebase.firebase_service import FirebaseService
import logging

logger = logging.getLogger(__name__)


# ── Verify Firebase ID Token ───────────────────────────────
async def verify_firebase_token(token: str) -> dict:
    """
    Verifies a Firebase ID token sent from the frontend.
    Returns decoded token payload with uid, email, etc.
    Raises HTTP 401 if invalid/expired.
    """
    try:
        decoded = firebase_auth.verify_id_token(token, check_revoked=True)
        return decoded
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please sign in again."
        )
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please sign in again."
        )
    except firebase_auth.InvalidIdTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed."
        )


# ── Extract Bearer Token ──────────────────────────────────
def extract_bearer_token(authorization: str) -> str:
    """
    Extracts token from 'Bearer <token>' header.
    Raises HTTP 401 if malformed.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or malformed. Use: Bearer <token>"
        )
    return authorization.split(" ", 1)[1].strip()


# ── Check Admin ───────────────────────────────────────────
async def verify_admin(uid: str):
    """
    Checks Firebase custom claims for admin role.
    Raises HTTP 403 if not admin.
    """
    try:
        user = firebase_auth.get_user(uid)
        claims = user.custom_claims or {}
        if not claims.get("admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin check error for uid {uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )


# ── Set Admin Claim ────────────────────────────────────────
def set_admin_claim(uid: str):
    """Set admin custom claim on a Firebase user."""
    firebase_auth.set_custom_user_claims(uid, {"admin": True})
    logger.info(f"Admin claim set for uid: {uid}")


# ── Cashfree Signature Verification ──────────────────────
import hmac
import hashlib
import base64
from core.config import settings


def verify_cashfree_signature(order_id: str, order_amount: str,
                               reference_id: str, tx_status: str,
                               payment_mode: str, tx_msg: str,
                               tx_time: str, signature: str) -> bool:
    """
    Verifies Cashfree payment callback signature.
    Prevents fake payment callbacks.
    """
    message = (order_id + order_amount + reference_id + tx_status
               + payment_mode + tx_msg + tx_time)
    secret = settings.CASHFREE_SECRET_KEY.encode("utf-8")
    computed = base64.b64encode(
        hmac.new(secret, message.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")
    return hmac.compare_digest(computed, signature)
