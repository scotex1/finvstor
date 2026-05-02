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

# ── Hardcoded fallback (replace after Render env vars work) ──
_HARDCODED_CREDS = {
    "type": "service_account",
    "project_id": "ai-vit-52666",
    "private_key_id": "134e41a9dcb9b1154ef782250a3309970caf5e43",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDEwEvk9vDDj/BR\n8x9IYQVHxCyO5vmfkBQoYeW60njGKbXk+dlbd0YBwr4S2viQK2DzLyHBsqLTF+b8\n1KpdnwC/vHfI5ujZvHJiAtdgpSomnfIwHGnYFDpuDoxlETiHyN+K8F0+TF5dJ3ZL\nik7fRR1tJdMFTEvybhATqkUl5HEP77M+RWKRw98B5emkP2S8YMwtm8uRawvij9Va\ncF0jVkTF3rNYx2I/CWwlFK6gZxr9BjySruoM3dNbbMavZRGDhGhfJNDIvHkHMaM4\n7oxYa8bU+AoogpMoE/7M7Fp0jiFhlsGpj++02ORzRYoqUYMoecXinXXnEDxABjQL\n4JdICs97AgMBAAECggEAMgicxDsv+uttt8lV2Tgi+Z8fna+LJ1KibaqHmzzOzcXp\npbML3UC1otj9MRpSP4dofi8sLG/bDEd1zDHgqTI4JIovA/4ElOphRB9o2gDmeS+N\nWULAf9yVB0vX1BPPBmjEwDZj3+XX0WSppogjio+u7gTCZwSCA8KNgBK6xuoS/nQJ\nYKGNqbZuEQUg3JLSoaDlmAZ77wBRX9UR0ACGYsSjZx41sZcAcb69MCwjHQmJ+hab\ngZAp5ggM6T0KcxFzqHWdX9hyLspl4rIBb5ss7uE2/S/DQP+YqqT253U0dk9z08Gw\n3MyaimKEnj1SSqnfADI8qIpnRWjDWb20gvXRhLNd0QKBgQD+D+DrT2g2+IVW0Hne\nGUyVAd7OLueaMGhTu5I69qG2GmaMeHc7K3AJpFXsPWwrKwEYw1R9nAM5+zfXgvTX\nhnQG2nLVWuxrCELQv+kWMEYT3JmxGamT3EebbrgC8hOmcBNuwxAG0VsxFR/4lLjE\nTWU2vZoKv1NiiicyAFsaAgWqbQKBgQDGQIDwno0PPNkAqQMyFdR7HK8DIzlO2xF0\nNaxMNk4pK6zLqwBG5GyEd3Jtk/h2qV3uMuUjYfxRCcnoA4zJPjREEKIZTT1CHOsi\nM0ZWJPsPX5xtwJ5LS/Upg2/Znxynzv1eqLo6j6rQkm9qE7xLjteInqcyQyvVpcHJ\nyMJXO4+whwKBgFuN207Q+cw9eMeVLyWTVl6oIuOIUZvl7+KkyIiJEjNuhh/+1XC0\nMZa36uLMK6vOvoFu+oadbyg42KHIJnV4lV1W4WTzdBkKDBHv5o5BbS+BIr2Icuy+\nx+tCVftxwxUKdGZI0wCx9zvT0gahiYfsIBo+70EKO4FaKc/CAxJ3QhVtAoGBAIcs\ngf4OTSW/mkJd+uTSh58trpLYGIIQ0nTHB+Sq/l4J/nab8MNliixD+UyHoNjfoEEC\niMO4Ur66iuVcTkkE1cQ3Bx9zT7pdV2FpTqL78gbIbTNUK1oxv0Z/7OqYF4S/mHhL\nWTcGsDQoNDlCnZdzHLh1XJDjxeaVb21zKjcqUE3PAoGAFpYmm2N0iPoj7lXVmgJJ\nPYXXDUr9hy4la8hwHjOoZ1S+A08DbUv7o6yf02IEdgcvvGBLAsMdYK4Fl3tNtmF/\nGBcvHXDXu32lgAeLb7U/9r81iSdbM5NVkO5rIJuAdyEc2tLI2w1fdPQP26Nl6F0V\n935eXF19Rkv+O6p8VZgxQUU=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@ai-vit-52666.iam.gserviceaccount.com",
    "client_id": "109190059134981226502",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40ai-vit-52666.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}


def initialize_firebase():
    global _initialized
    if _initialized or len(firebase_admin._apps):
        _initialized = True
        return

    cred = None
    project_id = None

    # Priority 1: Env var
    raw = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
    if raw:
        try:
            cred_dict = json.loads(raw)
            cred = credentials.Certificate(cred_dict)
            project_id = cred_dict.get("project_id")
            logger.info("✅ Firebase: loaded from env var")
        except Exception as e:
            logger.error(f"Env var parse error: {e}")

    # Priority 2: Hardcoded (temporary)
    if cred is None:
        try:
            cred = credentials.Certificate(_HARDCODED_CREDS)
            project_id = _HARDCODED_CREDS["project_id"]
            logger.info("✅ Firebase: loaded from hardcoded credentials")
        except Exception as e:
            logger.error(f"Hardcoded creds error: {e}")
            raise

    options = {"projectId": project_id} if project_id else {}
    firebase_admin.initialize_app(cred, options)
    _initialized = True
    logger.info(f"🔥 Firebase ready! Project: {project_id}")

