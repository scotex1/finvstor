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

    if _initialized or firebase_admin._apps:
        return

    firebase_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if firebase_json:
        try:
            cred_dict = json.loads(firebase_json)
            cred = credentials.Certificate(cred_dict)

            firebase_admin.initialize_app(
                cred,
                {
                    "projectId": settings.FIREBASE_PROJECT_ID
                }
            )

            _initialized = True
            logger.info("Firebase initialized from environment variable")
            return

        except Exception as e:
            raise RuntimeError(
                f"Invalid FIREBASE_CREDENTIALS_JSON: {e}"
            )

    cred_path = settings.FIREBASE_CREDENTIALS_PATH

    if not os.path.exists(cred_path):
        raise FileNotFoundError(
            f"Firebase credentials not found at: {cred_path}"
        )

    cred = credentials.Certificate(cred_path)

    firebase_admin.initialize_app(
        cred,
        {
            "projectId": settings.FIREBASE_PROJECT_ID
        }
    )

    _initialized = True
    logger.info("Firebase initialized from credentials file")

