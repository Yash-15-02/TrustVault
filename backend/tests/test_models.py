"""
Unit tests for SMSDetector and TransactionAnalyzer.

These tests mock the model loader so they don't need trained .pkl files.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


# ── SMSDetector indicator extraction tests ─────────────────────────────

class TestSMSIndicators:
    """Test the rule-based indicator extraction (no ML model needed)."""

    def _get_detector_class(self):
        # Import the class but prevent __init__ from loading models
        with patch("app.models.sms_detector.load_model"):
            from app.models.sms_detector import SMSDetector
            det = SMSDetector.__new__(SMSDetector)
        return det

    def test_urgency_detected(self):
        det = self._get_detector_class()
        result = det._extract_indicators("URGENT: Act now or your account will be blocked!")
        assert any("Urgency" in i for i in result)

    def test_suspicious_url_detected(self):
        det = self._get_detector_class()
        result = det._extract_indicators("Click http://evil.com/phish to verify")
        assert any("URL" in i for i in result)

    def test_prize_claim_detected(self):
        det = self._get_detector_class()
        result = det._extract_indicators("You have WON a lottery of Rs.50000!")
        assert any("Prize" in i or "money" in i for i in result)

    def test_credential_request_detected(self):
        det = self._get_detector_class()
        result = det._extract_indicators("Please verify your KYC and update your account")
        assert any("Credential" in i or "account" in i for i in result)

    def test_phone_callback_detected(self):
        det = self._get_detector_class()
        result = det._extract_indicators("Call 9876543210 immediately for your refund")
        assert any("Phone" in i for i in result)

    def test_brand_impersonation_detected(self):
        det = self._get_detector_class()
        result = det._extract_indicators(
            "URGENT: Your SBI account is suspended. Verify now!"
        )
        assert any("impersonation" in i.lower() for i in result)

    def test_clean_message_no_flags(self):
        det = self._get_detector_class()
        result = det._extract_indicators("Hey, are we still meeting today?")
        assert result == ["No obvious scam patterns"]

    def test_multiple_amounts_detected(self):
        det = self._get_detector_class()
        result = det._extract_indicators(
            "Pay Rs.500 now and claim Rs.50000 cashback!"
        )
        assert any("Multiple monetary" in i for i in result)


# ── TransactionAnalyzer risk factor tests ──────────────────────────────

class TestTransactionRiskFactors:
    """Test risk factor extraction (no ML model needed)."""

    def _get_analyzer(self):
        with patch("app.models.transaction_analyzer.load_model"):
            from app.models.transaction_analyzer import TransactionAnalyzer
            analyzer = TransactionAnalyzer.__new__(TransactionAnalyzer)
        return analyzer

    def test_high_amount_flagged(self):
        analyzer = self._get_analyzer()
        factors = analyzer._extract_risk_factors(75000, 0, 1, 2, 0.8)
        assert any("Very high" in f for f in factors)

    def test_new_receiver_noted(self):
        analyzer = self._get_analyzer()
        factors = analyzer._extract_risk_factors(1000, 1, 1, 0, 0.1)
        assert any("New/unknown" in f for f in factors)

    def test_known_receiver_noted(self):
        analyzer = self._get_analyzer()
        factors = analyzer._extract_risk_factors(1000, 0, 1, 0, 0.1)
        assert any("Known receiver" in f for f in factors)

    def test_high_velocity_flagged(self):
        analyzer = self._get_analyzer()
        factors = analyzer._extract_risk_factors(1000, 0, 10, 2, 0.8)
        assert any("Unusually high" in f or "velocity" in f.lower() for f in factors)

    def test_triple_flag_pattern(self):
        analyzer = self._get_analyzer()
        factors = analyzer._extract_risk_factors(50000, 1, 8, 2, 0.9)
        assert any("Triple-flag" in f for f in factors)

    def test_normal_transaction_clean(self):
        analyzer = self._get_analyzer()
        factors = analyzer._extract_risk_factors(500, 0, 1, 0, 0.05)
        assert any("typical" in f.lower() for f in factors)
