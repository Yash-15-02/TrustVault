"""
SMSDetector — classifies SMS messages as scam or legitimate.

Uses TF-IDF + LinearSVC loaded from trained artifacts, combined with
rule-based indicator extraction for explainability.
"""

import re

import numpy as np

from app.config import SMS_MODEL_PATH, VECTORIZER_PATH
from app.core.loader import load_model


class SMSDetector:
    def __init__(self):
        self.model = load_model(SMS_MODEL_PATH)
        self.vectorizer = load_model(VECTORIZER_PATH)

    def predict(self, message: str) -> dict:
        vec = self.vectorizer.transform([message])
        score = float(self.model.decision_function(vec)[0])

        # Sigmoid to map SVC decision score → probability-like confidence
        prob = float(1.0 / (1.0 + np.exp(-np.clip(score, -50, 50))))
        is_scam = score > 0

        indicators = self._extract_indicators(message)

        return {
            "is_scam": is_scam,
            "confidence": round(prob * 100.0, 1),
            "risk_score": int(round(prob * 100)),
            "decision_score": round(score, 4),
            "indicators": indicators,
            "indicator_count": len([i for i in indicators if i != "No obvious scam patterns"]),
        }

    def _extract_indicators(self, message: str) -> list:
        indicators = []
        lower = message.lower()

        # ── Urgency language ────────────────────────────────────────
        urgency = [
            "urgent", "immediately", "now", "today only", "final notice",
            "expiring", "expire", "blocked", "suspended", "deactivated",
            "action required", "last chance", "act now", "within 24",
        ]
        found_urgency = [w for w in urgency if w in lower]
        if found_urgency:
            indicators.append(
                f"Urgency language detected ({', '.join(found_urgency[:3])})"
            )

        # ── Suspicious URLs ─────────────────────────────────────────
        urls = re.findall(
            r"https?://[^\s]+|bit\.ly/\S+|tinyurl\.com/\S+|t\.co/\S+", lower
        )
        if urls:
            indicators.append(f"Suspicious URL(s) detected: {', '.join(urls[:2])}")

        # ── Money / prize claims ────────────────────────────────────
        money = [
            "won", "prize", "lakh", "crore", "lottery", "cashback",
            "refund", "reward", "bonus", "free",
        ]
        found_money = [w for w in money if w in lower]
        if found_money:
            indicators.append(
                f"Prize/money claim detected ({', '.join(found_money[:3])})"
            )

        # ── Credential harvesting ───────────────────────────────────
        creds = [
            "verify", "update", "kyc", "account", "card", "pin",
            "cvv", "password", "otp", "aadhaar", "pan card",
        ]
        found_creds = [w for w in creds if w in lower]
        if found_creds:
            indicators.append(
                f"Credential/account request ({', '.join(found_creds[:3])})"
            )

        # ── Phone number for callback ───────────────────────────────
        phones = re.findall(r"\b[6-9]\d{9}\b", message)
        if phones:
            indicators.append(f"Phone number for callback: {phones[0][:4]}XXXXXX")

        # ── Brand impersonation ─────────────────────────────────────
        brands = [
            "sbi", "hdfc", "icici", "paytm", "google pay", "phonepe",
            "amazon", "flipkart", "government", "police", "court",
            "rbi", "income tax", "aadhaar",
        ]
        found_brands = [b for b in brands if b in lower]
        if found_brands and (found_urgency or found_creds):
            indicators.append(
                f"Potential brand impersonation ({', '.join(found_brands[:2])})"
            )

        # ── Monetary amounts in text ────────────────────────────────
        amounts = re.findall(r"rs\.?\s*[\d,]+|₹\s*[\d,]+", lower)
        if len(amounts) >= 2:
            indicators.append("Multiple monetary amounts mentioned")

        return indicators if indicators else ["No obvious scam patterns"]
