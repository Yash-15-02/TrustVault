import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# ── Paths ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
MODEL_DIR = BACKEND_DIR / "data" / "trained_models"
DB_PATH = Path(os.getenv("DB_PATH", str(BACKEND_DIR / "data" / "trustvault.db")))
ALERT_LOG_DIR = BACKEND_DIR / "data" / "alerts"
EXPERIMENT_DIR = BACKEND_DIR / "data" / "experiments"

SMS_MODEL_PATH = str(MODEL_DIR / "sms_model.pkl")
SMS_META_PATH = str(MODEL_DIR / "sms_model_meta.json")
VECTORIZER_PATH = str(MODEL_DIR / "vectorizer.pkl")
TRANSACTION_MODEL_PATH = str(MODEL_DIR / "transaction_model.pkl")
TXN_META_PATH = str(MODEL_DIR / "transaction_model_meta.json")

# ── Risk thresholds ────────────────────────────────────────────────────
LOW_RISK = int(os.getenv("LOW_RISK", "40"))
HIGH_RISK = int(os.getenv("HIGH_RISK", "70"))
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", "80"))

# ── Alerts ──────────────────────────────────────────────────────────────
ENABLE_ALERTS = os.getenv("ENABLE_ALERTS", "true").lower() == "true"
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
ALERT_DEDUP_WINDOW_SEC = int(os.getenv("ALERT_DEDUP_WINDOW_SEC", "60"))

# ── Auth ────────────────────────────────────────────────────────────────
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
API_KEYS: dict[str, str] = {}
_raw_keys = os.getenv("API_KEYS", "")
if _raw_keys:
    for pair in _raw_keys.split(","):
        if ":" in pair:
            name, key = pair.split(":", 1)
            API_KEYS[key.strip()] = name.strip()

# ── Transaction model tuning ────────────────────────────────────────────
TXN_HIGH_PROB = float(os.getenv("TXN_HIGH_PROB", "0.65"))
TXN_MED_PROB = float(os.getenv("TXN_MED_PROB", "0.35"))

# ── API metadata ────────────────────────────────────────────────────────
API_TITLE = "TrustVault AI"
API_VERSION = "1.2.0"
