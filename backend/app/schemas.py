from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Request ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    amount: float = Field(gt=0, description="Transaction amount (must be positive)")
    is_new_receiver: int = Field(ge=0, le=1)
    transactions_today: int = Field(ge=0, le=500)
    message: str = Field(min_length=1, max_length=10000)

    @field_validator("is_new_receiver")
    @classmethod
    def receiver_binary(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError("is_new_receiver must be 0 or 1")
        return v


# ── Response ────────────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    risk_level: str
    risk_score: int
    recommendation: str
    explanation: str
    alert: Optional[Dict[str, Any]] = None
    delay_transaction: bool = False
    sms_analysis: Dict[str, Any]
    transaction_analysis: Dict[str, Any]
    response_time_ms: float = 0.0


# ── Audit / Stats ──────────────────────────────────────────────────────

class AuditEntry(BaseModel):
    id: int
    timestamp: str
    api_key_name: str
    risk_score: int
    risk_level: str
    recommendation: str
    alert_triggered: int
    response_time_ms: float


class StatsResponse(BaseModel):
    total_requests: int
    avg_risk_score: float
    avg_response_time_ms: float
    risk_distribution: Dict[str, int]
    alert_rate_pct: float
    last_24h_requests: int


class ModelInfo(BaseModel):
    file: Optional[str] = None
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    trained_at: Optional[str] = None
    sklearn_version: Optional[str] = None
    sklearn_runtime: Optional[str] = None
    test_accuracy: Optional[float] = None
    test_f1: Optional[float] = None
    cv_best_f1: Optional[float] = None
    status: Optional[str] = None
