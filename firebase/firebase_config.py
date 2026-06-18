# firebase/firebase_config.py

```python
"""
firebase/firebase_config.py — Firebase Admin SDK initialization
"""

import firebase_admin
from firebase_admin import credentials
from core.config import settings
import logging
import os
import json

logger = logging.getLogger(__name__)

_initialized = False


def initialize_firebase():
    """Initialize Firebase Admin SDK. Safe to call multiple times."""
    global _initialized

    if _initialized or len(firebase_admin._apps):
        return

    # 1. Try environment variable first (recommended for Render)
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
            logger.info(
                f"Firebase initialized from ENV: project={settings.FIREBASE_PROJECT_ID}"
            )
            return

        except Exception as e:
            raise RuntimeError(
                f"Failed to load Firebase credentials from FIREBASE_CREDENTIALS_JSON: {e}"
            )

    # 2. Fallback to local file
    cred_path = settings.FIREBASE_CREDENTIALS_PATH

    if not os.path.exists(cred_path):
        raise FileNotFoundError(
            f"Firebase credentials not found.\n"
            f"Checked ENV variable: FIREBASE_CREDENTIALS_JSON\n"
            f"Checked file path: {cred_path}"
        )

    cred = credentials.Certificate(cred_path)

    firebase_admin.initialize_app(
        cred,
        {
            "projectId": settings.FIREBASE_PROJECT_ID
        }
    )

    _initialized = True
    logger.info(
        f"Firebase initialized from file: project={settings.FIREBASE_PROJECT_ID}"
    )
```

