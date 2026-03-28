"""
Tests for the feature engineering module.

These are pure computation tests — no ML models required.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.utils.feature_engineering import (
    FEATURE_COLUMNS,
    enrich_features,
    process_training_data,
)


# ── enrich_features (inference-time) ────────────────────────────────────

class TestEnrichFeatures:
    def test_returns_all_columns(self):
        result = enrich_features(1000, 1, 3)
        assert set(result.keys()) == set(FEATURE_COLUMNS)

    def test_amount_preserved(self):
        result = enrich_features(5000, 0, 2)
        assert result["amount"] == 5000

    def test_amount_log_positive(self):
        result = enrich_features(100, 0, 1)
        assert result["amount_log"] == pytest.approx(np.log1p(100), rel=1e-6)

    def test_velocity_flag_low(self):
        result = enrich_features(100, 0, 3)
        assert result["velocity_flag"] == 0

    def test_velocity_flag_high(self):
        result = enrich_features(100, 0, 8)
        assert result["velocity_flag"] == 1

    def test_velocity_flag_boundary(self):
        assert enrich_features(100, 0, 5)["velocity_flag"] == 0
        assert enrich_features(100, 0, 6)["velocity_flag"] == 1

    def test_high_value_new_receiver_true(self):
        result = enrich_features(20000, 1, 1)
        assert result["high_value_new_receiver"] == 1

    def test_high_value_new_receiver_known(self):
        result = enrich_features(20000, 0, 1)
        assert result["high_value_new_receiver"] == 0

    def test_high_value_new_receiver_small_amount(self):
        result = enrich_features(500, 1, 1)
        assert result["high_value_new_receiver"] == 0

    def test_amount_per_txn_division(self):
        result = enrich_features(3000, 0, 3)
        assert result["amount_per_txn"] == 1000.0

    def test_amount_per_txn_zero_transactions(self):
        result = enrich_features(5000, 0, 0)
        assert result["amount_per_txn"] == 5000.0  # max(0, 1) = 1

    def test_amount_per_txn_log_computed(self):
        result = enrich_features(1000, 0, 1)
        expected = float(np.log1p(1000.0))
        assert result["amount_per_txn_log"] == pytest.approx(expected, rel=1e-6)


# ── process_training_data (bulk training) ───────────────────────────────

class TestProcessTrainingData:
    def _make_df(self, n=100):
        return pd.DataFrame({
            "Amount": np.random.uniform(10, 100000, n),
            "V1": np.random.normal(0, 1, n),
            "V2": np.random.normal(0, 1, n),
            "Class": np.random.choice([0, 1], n, p=[0.95, 0.05]),
        })

    def test_output_has_expected_columns(self):
        df = self._make_df()
        result = process_training_data(df)
        for col in FEATURE_COLUMNS:
            assert col in result.columns
        assert "Class" in result.columns

    def test_output_row_count_preserved(self):
        df = self._make_df(200)
        result = process_training_data(df)
        assert len(result) == 200

    def test_is_new_receiver_binary(self):
        df = self._make_df()
        result = process_training_data(df)
        assert set(result["is_new_receiver"].unique()).issubset({0, 1})

    def test_transactions_today_clamped(self):
        df = self._make_df()
        result = process_training_data(df)
        assert result["transactions_today"].min() >= 0
        assert result["transactions_today"].max() <= 20

    def test_no_nan_values(self):
        df = self._make_df()
        result = process_training_data(df)
        assert not result.isnull().any().any()

    def test_class_preserved(self):
        df = self._make_df()
        result = process_training_data(df)
        assert set(result["Class"].unique()).issubset({0, 1})
