"""
POST /analyze — unified SMS + transaction risk scoring endpoint.

Handles:
- SMS scam detection
- Transaction fraud scoring (on enriched features)
- Combined risk verdict
- Audit logging with response-time tracking
- Optional API-key authentication
- Alert triggering when score exceeds threshold
"""

import time

from fastapi import APIRouter, Depends, HTTPException

from app.config import ALERT_THRESHOLD, ENABLE_ALERTS, HIGH_RISK, LOW_RISK
from app.core.auth import verify_api_key
from app.core.database import log_request
from app.schemas import AnalyzeRequest
from app.services.sms_service import analyze_sms
from app.services.txn_service import analyze_transaction
from app.utils.alert import trigger_alert

router = APIRouter(tags=["analyze"])

WEIGHT_TXN = 0.6
WEIGHT_SMS = 0.4


def _build_explanation(sms: dict, txn: dict, recommendation: str) -> str:
    parts = []

    if sms.get("is_scam"):
        parts.append(
            f"SMS flagged as potential scam "
            f"(confidence: {sms['confidence']:.1f}%, "
            f"decision score: {sms.get('decision_score', 'N/A')})"
        )
        parts.extend(f"  • {i}" for i in sms.get("indicators", []))
    else:
        parts.append("SMS appears legitimate based on text analysis")
        if sms.get("indicator_count", 0) > 0:
            parts.append("  (minor flags noted — see indicators)")

    parts.append(
        f"\n{txn['risk_level']} — fraud probability {txn.get('fraud_probability', 'N/A')}"
    )
    parts.extend(f"  • {f}" for f in txn.get("risk_factors", []))

    parts.append(f"\nRecommendation: {recommendation}")
    return "\n".join(parts)


@router.post("/analyze")
def analyze_payment(
    data: AnalyzeRequest,
    api_key_name: str = Depends(verify_api_key),
):
    t0 = time.perf_counter()

    try:
        sms = analyze_sms(data.message)
        txn = analyze_transaction(
            data.amount, data.is_new_receiver, data.transactions_today,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    combined = int(WEIGHT_TXN * txn["risk_score"] + WEIGHT_SMS * sms["risk_score"])

    if combined >= HIGH_RISK:
        risk_level = "High"
        recommendation = "BLOCK — Manual review required"
    elif combined >= LOW_RISK:
        risk_level = "Medium"
        recommendation = "VERIFY — Additional authentication recommended"
    else:
        risk_level = "Low"
        recommendation = "APPROVE — Transaction can proceed"

    alert_data = None
    delay_transaction = False
    if ENABLE_ALERTS and combined >= ALERT_THRESHOLD:
        alert_data = trigger_alert(data.model_dump())
        delay_transaction = True

    explanation = _build_explanation(sms, txn, recommendation)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # ── Audit log ───────────────────────────────────────────────────
    try:
        log_request(
            request_payload=data.model_dump(),
            risk_score=combined,
            risk_level=risk_level,
            recommendation=recommendation,
            alert_triggered=alert_data is not None,
            response_time_ms=elapsed_ms,
            api_key_name=api_key_name,
        )
    except Exception:
        pass  # Never let audit failure break the API

    return {
        "risk_level": risk_level,
        "risk_score": combined,
        "recommendation": recommendation,
        "explanation": explanation,
        "alert": alert_data,
        "delay_transaction": delay_transaction,
        "sms_analysis": sms,
        "transaction_analysis": txn,
        "response_time_ms": round(elapsed_ms, 2),
    }
