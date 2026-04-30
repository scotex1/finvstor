"""
firebase/firebase_config.py — Firebase Admin SDK initialization
Supports both JSON string (Render) and file path (local dev)
"""

import firebase_admin
from firebase_admin import credentials
from core.config import settings
import logging
import json
import os

logger = logging.getLogger(__name__)

_initialized = False


def initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    
    Priority:
    1. FIREBASE_CREDENTIALS_JSON env var (paste full JSON — best for Render)
    2. FIREBASE_CREDENTIALS_PATH file (for local dev)
    """
    global _initialized
    if _initialized or len(firebase_admin._apps):
        _initialized = True
        return

    cred = None

    # ── Option 1: JSON string from environment variable ──
    # Recommended for Render — paste serviceAccountKey.json content as env var
    if settings.FIREBASE_CREDENTIALS_JSON:
        try:
            cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
            cred = credentials.Certificate(cred_dict)
            logger.info("Firebase: loaded credentials from FIREBASE_CREDENTIALS_JSON env var")
        except json.JSONDecodeError as e:
            raise ValueError(
                f"FIREBASE_CREDENTIALS_JSON is not valid JSON: {e}\n"
                "Make sure you pasted the entire serviceAccountKey.json content."
            )

    # ── Option 2: File path (local development) ──────────
    elif os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        logger.info(f"Firebase: loaded credentials from file: {settings.FIREBASE_CREDENTIALS_PATH}")

    else:
        raise FileNotFoundError(
            "Firebase credentials not found!\n\n"
            "For Render deployment:\n"
            "  Set env var FIREBASE_CREDENTIALS_JSON = (paste serviceAccountKey.json content)\n\n"
            "For local development:\n"
            "  Place serviceAccountKey.json at: firebase/serviceAccountKey.json\n\n"
            "Download from: Firebase Console → Project Settings → Service Accounts → Generate new private key"
        )

    firebase_admin.initialize_app(cred, {
        "projectId": settings.FIREBASE_PROJECT_ID
    })
    _initialized = True
    logger.info(f"✅ Firebase initialized | project: {settings.FIREBASE_PROJECT_ID}")

