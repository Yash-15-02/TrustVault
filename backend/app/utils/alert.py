"""
Pluggable alert system for high-risk transactions.

Three alert channels fire in parallel:

1. **Console** — structured JSON log via Python logging (always on)
2. **File**    — append to ``data/alerts/alert_log.jsonl``
3. **Webhook** — HTTP POST to ``ALERT_WEBHOOK_URL`` (when configured)

Includes deduplication: the same (amount, message_snippet) pair won't
fire more than once within ``ALERT_DEDUP_WINDOW_SEC`` seconds.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import (
    ALERT_DEDUP_WINDOW_SEC,
    ALERT_LOG_DIR,
    ALERT_WEBHOOK_URL,
)

logger = logging.getLogger("trustvault.alerts")

# Simple in-memory dedup cache: hash → timestamp
_recent_alerts: dict[str, float] = {}


def _dedup_key(payload: dict) -> str:
    raw = f"{payload.get('amount', '')}|{str(payload.get('message', ''))[:60]}"
    return hashlib.md5(raw.encode()).hexdigest()


def _is_duplicate(key: str) -> bool:
    now = time.time()
    # Prune old entries
    expired = [k for k, ts in _recent_alerts.items() if now - ts > ALERT_DEDUP_WINDOW_SEC]
    for k in expired:
        del _recent_alerts[k]

    if key in _recent_alerts:
        return True
    _recent_alerts[key] = now
    return False


def trigger_alert(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Fire alerts across all configured channels.

    Returns the alert object to be included in the API response.
    """
    dup_key = _dedup_key(payload)
    is_dup = _is_duplicate(dup_key)

    alert_obj = {
        "triggered": True,
        "deduplicated": is_dup,
        "type": "HIGH_RISK_TRANSACTION",
        "severity": "critical",
        "title": "TrustVault — High-Risk Payment Alert",
        "message": (
            "A transaction with high-risk indicators has been flagged. "
            "Review before proceeding."
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actions": [
            "In-app warning shown to payer",
            "Delay / cooldown flag set",
            "Audit log entry created",
        ],
        "amount": payload.get("amount"),
        "snippet": (payload.get("message") or "")[:120],
    }

    if is_dup:
        logger.info("Duplicate alert suppressed (key=%s)", dup_key[:8])
        return alert_obj

    # ── 1. Console (structured JSON log) ────────────────────────────
    logger.warning(
        "HIGH-RISK ALERT | amount=%.2f | snippet=%s",
        payload.get("amount", 0),
        (payload.get("message") or "")[:80],
    )

    # ── 2. File log ─────────────────────────────────────────────────
    _log_to_file(alert_obj)

    # ── 3. Webhook ──────────────────────────────────────────────────
    if ALERT_WEBHOOK_URL:
        _fire_webhook(alert_obj)
        alert_obj["actions"].append(f"Webhook fired → {ALERT_WEBHOOK_URL}")

    return alert_obj


def _log_to_file(alert: dict) -> None:
    """Append alert as a JSON line to the alert log file."""
    try:
        ALERT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = ALERT_LOG_DIR / "alert_log.jsonl"
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert) + "\n")
    except Exception:
        logger.exception("Failed to write alert log file")


def _fire_webhook(alert: dict) -> None:
    """POST alert payload to the configured webhook URL."""
    try:
        resp = httpx.post(
            ALERT_WEBHOOK_URL,
            json=alert,
            timeout=5.0,
            headers={"Content-Type": "application/json"},
        )
        logger.info("Webhook response: %s %s", resp.status_code, resp.reason_phrase)
    except Exception:
        logger.exception("Webhook delivery failed for %s", ALERT_WEBHOOK_URL)
