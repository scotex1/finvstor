"""
firebase/firebase_config.py — Firebase Admin SDK initialization
"""

import os
import json
import logging

import firebase_admin
from firebase_admin import credentials

from core.config import settings

logger = logging.getLogger(__name__)

_initialized = False


def initialize_firebase():
    global _initialized

    # ✅ Already initialized protection
    if _initialized or firebase_admin._apps:
        return firebase_admin.get_app()

    firebase_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    try:
        # =========================
        # ENV VARIABLE METHOD (RENDER)
        # =========================
        if firebase_json:
            cred_dict = json.loads(firebase_json)

            # 🔥 FIX 1: Ensure private_key newline fix
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

            cred = credentials.Certificate(cred_dict)

        # =========================
        # LOCAL FILE METHOD
        # =========================
        else:
            cred_path = settings.FIREBASE_CREDENTIALS_PATH

            if not os.path.exists(cred_path):
                raise FileNotFoundError(
                    f"Firebase credentials not found at: {cred_path}"
                )

            cred = credentials.Certificate(cred_path)

        # =========================
        # INIT APP
        # =========================
        firebase_admin.initialize_app(
            cred,
            {
                "projectId": settings.FIREBASE_PROJECT_ID
            }
        )

        _initialized = True
        logger.info("Firebase initialized successfully")

        return firebase_admin.get_app()

    except Exception as e:
        logger.exception("Firebase initialization failed")
        raise RuntimeError(f"Firebase init error: {str(e)}")

