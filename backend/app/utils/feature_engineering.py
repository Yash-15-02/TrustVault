"""
Feature engineering for TrustVault transaction fraud detection.

Two entry points:
- ``process_training_data(df)`` — bulk transform a raw credit-card CSV
  into the enriched feature set used for training.
- ``enrich_features(amount, is_new_receiver, transactions_today)`` —
  compute the *same* derived features from the three API-facing inputs
  at inference time.  Returns a dict suitable for ``pd.DataFrame([...])``
  so the model sees identical columns.
"""

import numpy as np
import pandas as pd


# ── Derived feature helpers (single-row, no DataFrame needed) ───────────

def _amount_log(amount: float) -> float:
    return float(np.log1p(amount))


def _velocity_flag(transactions_today: int) -> int:
    return int(transactions_today > 5)


def _high_value_new_receiver(amount: float, is_new_receiver: int) -> int:
    return int(amount > 10_000) * is_new_receiver


def _amount_per_txn(amount: float, transactions_today: int) -> float:
    return amount / max(transactions_today, 1)


def _amount_per_txn_log(amount: float, transactions_today: int) -> float:
    return float(np.log1p(_amount_per_txn(amount, transactions_today)))


# The canonical column order the model expects
FEATURE_COLUMNS = [
    "amount",
    "is_new_receiver",
    "transactions_today",
    "amount_log",
    "velocity_flag",
    "high_value_new_receiver",
    "amount_per_txn",
    "amount_per_txn_log",
]


def enrich_features(
    amount: float,
    is_new_receiver: int,
    transactions_today: int,
) -> dict:
    """
    Build the full feature vector for a *single* inference request.

    Returns a dict whose keys exactly match ``FEATURE_COLUMNS``.
    """
    return {
        "amount": amount,
        "is_new_receiver": is_new_receiver,
        "transactions_today": transactions_today,
        "amount_log": _amount_log(amount),
        "velocity_flag": _velocity_flag(transactions_today),
        "high_value_new_receiver": _high_value_new_receiver(amount, is_new_receiver),
        "amount_per_txn": _amount_per_txn(amount, transactions_today),
        "amount_per_txn_log": _amount_per_txn_log(amount, transactions_today),
    }


def process_training_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform a raw credit-card-style DataFrame (with ``Amount``, ``V1``,
    ``V2``, ``Class`` columns) into the enriched feature DataFrame used
    for training.

    Mapping logic:
    - ``amount``  ← ``Amount``
    - ``is_new_receiver``  ← 1 when ``V1 > 0`` (proxy heuristic)
    - ``transactions_today``  ← ``|V2| * 3`` clamped to [0, 20]
    - Plus all derived features computed by ``enrich_features()``.
    """
    out = pd.DataFrame()
    out["amount"] = df["Amount"].astype(float)
    out["is_new_receiver"] = (df["V1"] > 0).astype(int)
    out["transactions_today"] = (
        df["V2"].abs().mul(3).round().astype(int).clip(0, 20)
    )

    # Derived features (vectorised)
    out["amount_log"] = np.log1p(out["amount"])
    out["velocity_flag"] = (out["transactions_today"] > 5).astype(int)
    out["high_value_new_receiver"] = (
        (out["amount"] > 10_000).astype(int) * out["is_new_receiver"]
    )
    out["amount_per_txn"] = out["amount"] / out["transactions_today"].clip(lower=1)
    out["amount_per_txn_log"] = np.log1p(out["amount_per_txn"])

    out["Class"] = df["Class"].astype(int)
    return out
