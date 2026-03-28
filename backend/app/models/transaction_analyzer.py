"""
TransactionAnalyzer — predicts fraud probability on enriched features.

At inference time, the three raw API inputs are expanded into 8
features by ``enrich_features()`` so the model sees the same columns
it was trained on.
"""

import pandas as pd

from app.config import TRANSACTION_MODEL_PATH, TXN_HIGH_PROB, TXN_MED_PROB
from app.core.loader import load_model
from app.utils.feature_engineering import FEATURE_COLUMNS, enrich_features


class TransactionAnalyzer:
    def __init__(self):
        self.model = load_model(TRANSACTION_MODEL_PATH)
        self.risk_labels = ["Low Risk", "Medium Risk", "High Risk"]

    def analyze(self, amount: float, is_new_receiver: int, transactions_today: int) -> dict:
        # Build the full feature vector (same columns as training)
        features = enrich_features(amount, is_new_receiver, transactions_today)
        X = pd.DataFrame([features], columns=FEATURE_COLUMNS)

        proba = self.model.predict_proba(X)[0]
        fraud_p = float(proba[1])

        if fraud_p >= TXN_HIGH_PROB:
            risk_idx = 2
        elif fraud_p >= TXN_MED_PROB:
            risk_idx = 1
        else:
            risk_idx = 0

        risk_score = int(round(fraud_p * 100))
        confidence = float(max(proba) * 100.0)

        risk_factors = self._extract_risk_factors(
            amount, is_new_receiver, transactions_today, risk_idx, fraud_p,
        )

        return {
            "risk_level": self.risk_labels[risk_idx],
            "risk_score": risk_score,
            "confidence": confidence,
            "fraud_probability": round(fraud_p, 4),
            "features_used": FEATURE_COLUMNS,
            "risk_factors": risk_factors,
        }

    def _extract_risk_factors(
        self,
        amount: float,
        is_new_receiver: int,
        transactions_today: int,
        risk_idx: int,
        fraud_p: float,
    ) -> list:
        factors = []

        # ── Amount analysis ─────────────────────────────────────────
        if amount > 50_000:
            factors.append(f"Very high transaction amount (₹{amount:,.0f})")
        elif amount > 10_000:
            factors.append(f"High transaction amount (₹{amount:,.0f})")
        else:
            factors.append(f"Normal transaction amount (₹{amount:,.0f})")

        # ── Receiver trust ──────────────────────────────────────────
        if is_new_receiver:
            factors.append("New/unknown receiver (first-time payment)")
        else:
            factors.append("Known receiver (previous transactions exist)")

        # ── Velocity ────────────────────────────────────────────────
        if transactions_today >= 7:
            factors.append(
                f"Unusually high activity ({transactions_today} transactions today)"
            )
        elif transactions_today >= 4:
            factors.append(
                f"Elevated transaction frequency ({transactions_today} today)"
            )
        else:
            factors.append(
                f"Normal activity ({transactions_today} transactions today)"
            )

        # ── Compound / interaction patterns ─────────────────────────
        if risk_idx == 2:
            if amount > 30_000 and is_new_receiver:
                factors.append(
                    "⚠ Large payment to new receiver — elevated fraud pattern"
                )
            if transactions_today > 5:
                factors.append("⚠ Potential account takeover pattern (high velocity)")
            if amount > 10_000 and transactions_today > 5 and is_new_receiver:
                factors.append(
                    "⚠ Triple-flag: high amount + new receiver + high velocity"
                )
        elif risk_idx == 1:
            factors.append("Elevated risk — additional verification recommended")
        else:
            factors.append("Transaction appears typical for this profile")

        return factors
