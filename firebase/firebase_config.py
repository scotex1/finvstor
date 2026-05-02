"""
firebase/firebase_config.py — Firebase Admin SDK initialization
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

    # ── Option 1: JSON string from env var (Render) ──────
    cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()

    if cred_json:
        try:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            logger.info("✅ Firebase: credentials loaded from FIREBASE_CREDENTIALS_JSON")
        except json.JSONDecodeError as e:
            raise ValueError(
                f"FIREBASE_CREDENTIALS_JSON is not valid JSON: {e}\n"
                "Paste the ENTIRE serviceAccountKey.json content as the value."
            )

    # ── Option 2: Local file ──────────────────────────────
    else:
        paths = [
            "firebase/serviceAccountKey.json",
            "serviceAccountKey.json",
        ]
        for path in paths:
            if os.path.exists(path):
                cred = credentials.Certificate(path)
                logger.info(f"✅ Firebase: credentials loaded from file: {path}")
                break

    if cred is None:
        # Debug: print what env vars are available
        all_vars = [k for k in os.environ.keys()]
        logger.error(f"Available env vars: {all_vars}")
        raise FileNotFoundError(
            "Firebase credentials not found!\n"
            "Set env var: FIREBASE_CREDENTIALS_JSON = (full JSON content)\n"
            f"Available env vars: {all_vars}"
        )

    project_id = os.environ.get("FIREBASE_PROJECT_ID", "")

    init_options = {}
    if project_id:
        init_options["projectId"] = project_id

    firebase_admin.initialize_app(cred, init_options)
    _initialized = True
    logger.info("🔥 Firebase initialized successfully!")

