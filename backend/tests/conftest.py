"""Shared pytest fixtures for TrustVault tests."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("ENABLE_ALERTS", "true")
os.environ.setdefault("REQUIRE_AUTH", "false")
os.environ["DB_PATH"] = str(BACKEND / "data" / "test_trustvault.db")


@pytest.fixture(autouse=True)
def _clean_test_db():
    """Reset the database module between tests."""
    import app.core.database as db_mod

    # Close any existing connection
    if db_mod._connection is not None:
        try:
            db_mod._connection.close()
        except Exception:
            pass
        db_mod._connection = None

    db = Path(os.environ["DB_PATH"])
    try:
        db.unlink(missing_ok=True)
    except PermissionError:
        pass

    yield

    # Cleanup after test
    if db_mod._connection is not None:
        try:
            db_mod._connection.close()
        except Exception:
            pass
        db_mod._connection = None
    try:
        db.unlink(missing_ok=True)
    except PermissionError:
        pass


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_low_risk():
    return {
        "amount": 500.0,
        "is_new_receiver": 0,
        "transactions_today": 1,
        "message": "Your OTP is 123456. Valid for 10 minutes. Do not share.",
    }


@pytest.fixture
def sample_high_risk():
    return {
        "amount": 95000.0,
        "is_new_receiver": 1,
        "transactions_today": 12,
        "message": (
            "URGENT: Your SBI account will be BLOCKED! "
            "Click bit.ly/fraud123 to verify NOW! "
            "Your KYC is pending. Call 9876543210"
        ),
    }


@pytest.fixture
def sample_medium_risk():
    return {
        "amount": 15000.0,
        "is_new_receiver": 1,
        "transactions_today": 3,
        "message": "Payment of Rs.15000 received. Thank you.",
    }
