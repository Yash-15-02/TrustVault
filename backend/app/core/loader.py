"""
Model loader with version / metadata awareness.

Each trained model can have an optional ``<name>_meta.json`` sidecar
containing training timestamp, sklearn version, hyperparams, and
evaluation scores.  The loader reads both and exposes them via
``get_model_info()``.
"""

import json
import logging
from pathlib import Path

import joblib
import sklearn

logger = logging.getLogger("trustvault.loader")

_loaded_meta: dict[str, dict] = {}


def load_model(path: str):
    """Load a joblib model and its optional metadata sidecar."""
    p = Path(path)
    try:
        model = joblib.load(p)
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Model file not found: {p}. Train models first (see backend/training/)."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Error loading model from {p}: {e}") from e

    # ── sidecar metadata ────────────────────────────────────────────
    meta_path = p.with_name(p.stem + "_meta.json")
    meta: dict = {"file": p.name, "status": "loaded"}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["file"] = p.name

            trained_sklearn = meta.get("sklearn_version", "")
            if trained_sklearn and trained_sklearn != sklearn.__version__:
                logger.warning(
                    "Model %s was trained with sklearn %s but runtime is %s — "
                    "predictions may differ.",
                    p.name,
                    trained_sklearn,
                    sklearn.__version__,
                )
        except Exception:
            logger.warning("Could not read metadata from %s", meta_path)

    meta["sklearn_runtime"] = sklearn.__version__
    _loaded_meta[p.stem] = meta
    logger.info("Loaded model %s", p.name)
    return model


def get_models_info() -> dict[str, dict]:
    """Return metadata for every model that has been loaded so far."""
    return dict(_loaded_meta)
