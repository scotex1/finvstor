"""
firebase/firebase_config.py
"""
import firebase_admin
from firebase_admin import credentials
import logging
import json
import os

logger = logging.getLogger(__name__)
_initialized = False


def initialize_firebase():
    global _initialized
    if _initialized or len(firebase_admin._apps):
        _initialized = True
        return

    cred = None
    project_id = None

    # Env var se load karo (Render pe FIREBASE_CREDENTIALS_JSON set karo)
    raw = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
    if raw:
        try:
            cred_dict = json.loads(raw)
            cred = credentials.Certificate(cred_dict)
            project_id = cred_dict.get("project_id")
            logger.info("✅ Firebase: loaded from FIREBASE_CREDENTIALS_JSON")
        except Exception as e:
            logger.error(f"Env var parse error: {e}")
            raise

    if cred is None:
        raise RuntimeError(
            "❌ FIREBASE_CREDENTIALS_JSON env var not set!\n"
            "Render → Environment → Add: FIREBASE_CREDENTIALS_JSON = (full JSON)"
        )

    options = {"projectId": project_id} if project_id else {}
    firebase_admin.initialize_app(cred, options)
    _initialized = True
    logger.info(f"🔥 Firebase ready! Project: {project_id}")
