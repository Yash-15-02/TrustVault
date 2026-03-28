"""
SQLite audit log for every /analyze request.
Zero external dependencies — uses stdlib sqlite3 in a thread-safe way.
"""

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import DB_PATH

_lock = threading.Lock()
_connection: sqlite3.Connection | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    NOT NULL,
    api_key_name    TEXT    DEFAULT 'anonymous',
    request_payload TEXT    NOT NULL,
    risk_score      INTEGER NOT NULL,
    risk_level      TEXT    NOT NULL,
    recommendation  TEXT    NOT NULL,
    alert_triggered INTEGER NOT NULL DEFAULT 0,
    response_time_ms REAL   NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_risk_level ON audit_log(risk_level);
"""


def init_db() -> None:
    """Create the database and tables if they don't exist."""
    global _connection
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    _connection.row_factory = sqlite3.Row
    _connection.executescript(_SCHEMA)
    _connection.commit()


@contextmanager
def _get_db():
    """Thread-safe access to the shared connection."""
    if _connection is None:
        init_db()
    with _lock:
        yield _connection


def log_request(
    *,
    request_payload: dict,
    risk_score: int,
    risk_level: str,
    recommendation: str,
    alert_triggered: bool,
    response_time_ms: float,
    api_key_name: str = "anonymous",
) -> int:
    """Insert an audit row. Returns the row id."""
    ts = datetime.now(timezone.utc).isoformat()
    with _get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO audit_log
                (timestamp, api_key_name, request_payload, risk_score,
                 risk_level, recommendation, alert_triggered, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                api_key_name,
                json.dumps(request_payload),
                risk_score,
                risk_level,
                recommendation,
                int(alert_triggered),
                round(response_time_ms, 2),
            ),
        )
        conn.commit()
        return cur.lastrowid


def get_recent_logs(limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent audit entries."""
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict[str, Any]:
    """Aggregated statistics over all audited requests."""
    with _get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        if total == 0:
            return {
                "total_requests": 0,
                "avg_risk_score": 0,
                "avg_response_time_ms": 0,
                "risk_distribution": {},
                "alert_rate_pct": 0,
                "last_24h_requests": 0,
            }

        avg_score = conn.execute(
            "SELECT AVG(risk_score) FROM audit_log"
        ).fetchone()[0]
        avg_time = conn.execute(
            "SELECT AVG(response_time_ms) FROM audit_log"
        ).fetchone()[0]
        alerts = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE alert_triggered = 1"
        ).fetchone()[0]

        dist_rows = conn.execute(
            "SELECT risk_level, COUNT(*) as cnt FROM audit_log GROUP BY risk_level"
        ).fetchall()
        distribution = {r["risk_level"]: r["cnt"] for r in dist_rows}

        recent = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE timestamp > datetime('now', '-1 day')"
        ).fetchone()[0]

    return {
        "total_requests": total,
        "avg_risk_score": round(avg_score, 1),
        "avg_response_time_ms": round(avg_time, 2),
        "risk_distribution": distribution,
        "alert_rate_pct": round((alerts / total) * 100, 1) if total else 0,
        "last_24h_requests": recent,
    }
