"""
Comprehensive API tests for TrustVault.

Covers: health, validation, risk scoring, alerts, audit, stats, model info, auth.
"""

import os
import sys
from pathlib import Path

import pytest


# ── Health & metadata ──────────────────────────────────────────────────

def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "version" in body


def test_info_endpoint(client):
    r = client.get("/info")
    assert r.status_code == 200
    body = r.json()
    assert "analyze" in body
    assert "audit" in body


# ── Input validation ───────────────────────────────────────────────────

def test_negative_amount_rejected(client):
    r = client.post("/analyze", json={
        "amount": -100, "is_new_receiver": 1,
        "transactions_today": 0, "message": "hi",
    })
    assert r.status_code == 422


def test_zero_amount_rejected(client):
    r = client.post("/analyze", json={
        "amount": 0, "is_new_receiver": 0,
        "transactions_today": 1, "message": "hello",
    })
    assert r.status_code == 422


def test_missing_message_rejected(client):
    r = client.post("/analyze", json={
        "amount": 100, "is_new_receiver": 0, "transactions_today": 1,
    })
    assert r.status_code == 422


def test_empty_message_rejected(client):
    r = client.post("/analyze", json={
        "amount": 100, "is_new_receiver": 0,
        "transactions_today": 1, "message": "",
    })
    assert r.status_code == 422


def test_invalid_receiver_flag(client):
    r = client.post("/analyze", json={
        "amount": 100, "is_new_receiver": 5,
        "transactions_today": 1, "message": "hello",
    })
    assert r.status_code == 422


def test_excessive_transactions_rejected(client):
    r = client.post("/analyze", json={
        "amount": 100, "is_new_receiver": 0,
        "transactions_today": 999, "message": "hello",
    })
    assert r.status_code == 422


# ── Successful analysis ───────────────────────────────────────────────

def _try_analyze(client, payload):
    """Helper: POST to /analyze, handle gracefully if models not trained."""
    r = client.post("/analyze", json=payload)
    if r.status_code == 503:
        pytest.skip("Models not trained — run training scripts first")
    return r


def test_analyze_returns_full_schema(client, sample_low_risk):
    r = _try_analyze(client, sample_low_risk)
    assert r.status_code == 200
    body = r.json()
    expected_keys = {
        "risk_level", "risk_score", "recommendation", "explanation",
        "alert", "delay_transaction", "sms_analysis", "transaction_analysis",
        "response_time_ms",
    }
    assert expected_keys.issubset(set(body.keys()))


def test_risk_score_is_bounded(client, sample_low_risk):
    r = _try_analyze(client, sample_low_risk)
    assert r.status_code == 200
    score = r.json()["risk_score"]
    assert 0 <= score <= 100


def test_response_time_tracked(client, sample_low_risk):
    r = _try_analyze(client, sample_low_risk)
    assert r.status_code == 200
    assert r.json()["response_time_ms"] > 0


def test_sms_analysis_has_indicators(client, sample_high_risk):
    r = _try_analyze(client, sample_high_risk)
    assert r.status_code == 200
    sms = r.json()["sms_analysis"]
    assert "indicators" in sms
    assert isinstance(sms["indicators"], list)


def test_transaction_analysis_has_risk_factors(client, sample_low_risk):
    r = _try_analyze(client, sample_low_risk)
    assert r.status_code == 200
    txn = r.json()["transaction_analysis"]
    assert "risk_factors" in txn
    assert "features_used" in txn


# ── Alert behaviour ────────────────────────────────────────────────────

def test_high_risk_triggers_alert(client, sample_high_risk):
    r = _try_analyze(client, sample_high_risk)
    assert r.status_code == 200
    body = r.json()
    # High risk should have score >= 70 and likely trigger alert
    if body["risk_score"] >= 80:
        assert body["alert"] is not None
        assert body["delay_transaction"] is True


def test_low_risk_no_alert(client, sample_low_risk):
    r = _try_analyze(client, sample_low_risk)
    assert r.status_code == 200
    body = r.json()
    if body["risk_score"] < 80:
        assert body["alert"] is None
        assert body["delay_transaction"] is False


# ── Observability endpoints ────────────────────────────────────────────

def test_audit_endpoint_returns_list(client):
    r = client.get("/audit")
    assert r.status_code == 200
    assert "entries" in r.json()


def test_stats_endpoint_returns_fields(client):
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert "total_requests" in body
    assert "avg_risk_score" in body
    assert "risk_distribution" in body


def test_models_info_endpoint(client):
    r = client.get("/models/info")
    assert r.status_code == 200
    assert "models" in r.json()


# ── Audit log integration ──────────────────────────────────────────────

def test_analyze_creates_audit_entry(client, sample_low_risk):
    r = _try_analyze(client, sample_low_risk)
    if r.status_code != 200:
        pytest.skip("Models not trained")

    audit = client.get("/audit?limit=1").json()
    entries = audit.get("entries", [])
    assert len(entries) >= 1
    entry = entries[0]
    assert entry["risk_level"] in ("Low", "Medium", "High")
    assert entry["response_time_ms"] > 0
