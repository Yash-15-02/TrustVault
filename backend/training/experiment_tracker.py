"""
Lightweight experiment tracker — no MLflow dependency.

Each training run is recorded as a JSON object appended to
``data/experiments/runs.json``.  Call ``log_run()`` from training
scripts and ``load_runs()`` / ``print_comparison()`` to review.
"""

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sklearn

from app.config import EXPERIMENT_DIR


def _ensure_dir() -> Path:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    return EXPERIMENT_DIR / "runs.json"


def dataset_hash(path: str | Path, sample_bytes: int = 65_536) -> str:
    """Fast, deterministic hash of the first ``sample_bytes`` of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(sample_bytes))
    return h.hexdigest()[:12]


def log_run(
    *,
    model_name: str,
    model_type: str,
    hyperparams: dict[str, Any],
    cv_scores: dict[str, float] | None = None,
    test_scores: dict[str, float],
    dataset_path: str | Path,
    notes: str = "",
) -> dict:
    """Append a run record and return it."""
    run = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_name": model_name,
        "model_type": model_type,
        "hyperparams": hyperparams,
        "cv_scores": cv_scores,
        "test_scores": test_scores,
        "dataset_hash": dataset_hash(dataset_path),
        "sklearn_version": sklearn.__version__,
        "python_version": platform.python_version(),
        "notes": notes,
    }

    log_path = _ensure_dir()
    runs: list[dict] = []
    if log_path.exists():
        try:
            runs = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            runs = []

    runs.append(run)
    log_path.write_text(json.dumps(runs, indent=2), encoding="utf-8")
    return run


def load_runs() -> list[dict]:
    """Return all recorded runs (newest last)."""
    log_path = _ensure_dir()
    if not log_path.exists():
        return []
    try:
        return json.loads(log_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return []


def print_comparison() -> None:
    """Pretty-print a comparison table of all runs."""
    runs = load_runs()
    if not runs:
        print("No experiment runs recorded yet.")
        return

    header = f"{'Run ID':<20} {'Model':<18} {'Type':<30} {'Test Acc':>9} {'Test F1':>8} {'CV Mean':>8}"
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))
    for r in runs:
        ts = r.get("test_scores", {})
        cv = r.get("cv_scores", {})
        print(
            f"{r['run_id']:<20} "
            f"{r['model_name']:<18} "
            f"{r['model_type']:<30} "
            f"{ts.get('accuracy', 0):>8.4f} "
            f"{ts.get('f1', 0):>8.4f} "
            f"{cv.get('mean', 0):>8.4f}"
        )
    print("=" * len(header) + "\n")
