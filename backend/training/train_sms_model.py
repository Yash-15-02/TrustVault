"""
Train SMS scam/spam detector.

Pipeline: TF-IDF → LinearSVC with GridSearchCV + stratified 5-fold CV.

Run:  cd backend && python training/train_sms_model.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from training.experiment_tracker import log_run, print_comparison  # noqa: E402

RAW = BACKEND / "data" / "raw" / "sms_spam.csv"
OUT_DIR = BACKEND / "data" / "trained_models"


def main():
    if not RAW.exists():
        print(f"Missing {RAW}")
        print("Generate it:  python data/raw/generate_datasets.py")
        sys.exit(1)

    data = pd.read_csv(RAW)
    if "message" not in data.columns or "label" not in data.columns:
        print("Expected columns: message, label  (ham/spam)")
        sys.exit(1)

    data["label"] = (
        data["label"].astype(str).str.strip().str.lower().map({"ham": 0, "spam": 1})
    )
    data = data.dropna(subset=["message", "label"])

    X = data["message"].astype(str)
    y = data["label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    # ── Pipeline + Grid Search ──────────────────────────────────────
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", lowercase=True)),
        ("clf", LinearSVC(class_weight="balanced", random_state=42)),
    ])

    param_grid = {
        "tfidf__max_features": [3000, 5000, 8000],
        "tfidf__ngram_range": [(1, 1), (1, 2)],
        "clf__C": [0.1, 0.5, 1.0, 2.0],
        "clf__max_iter": [5000],
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    print("Running GridSearchCV (5-fold) …")
    grid = GridSearchCV(
        pipeline,
        param_grid,
        cv=cv,
        scoring="f1",
        n_jobs=-1,
        verbose=1,
        refit=True,
    )
    grid.fit(X_train, y_train)

    print(f"\nBest params : {grid.best_params_}")
    print(f"Best CV F1  : {grid.best_score_:.4f}")

    # ── Evaluate on held-out test set ───────────────────────────────
    best = grid.best_estimator_
    y_pred = best.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)

    print(f"\n=== Test Results ===")
    print(f"Accuracy  : {acc:.4f}")
    print(f"Precision : {prec:.4f}")
    print(f"Recall    : {rec:.4f}")
    print(f"F1        : {f1:.4f}")
    print(classification_report(y_test, y_pred, target_names=["Safe", "Scam"]))
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))

    # ── Save model + vectorizer separately (backward compat) ────────
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Extract components from pipeline for the existing loader interface
    final_vectorizer = best.named_steps["tfidf"]
    final_clf = best.named_steps["clf"]

    joblib.dump(final_clf, OUT_DIR / "sms_model.pkl")
    joblib.dump(final_vectorizer, OUT_DIR / "vectorizer.pkl")

    # ── Save metadata sidecar ───────────────────────────────────────
    meta = {
        "model_name": "sms_detector",
        "model_type": "TF-IDF + LinearSVC (GridSearchCV)",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "best_params": grid.best_params_,
        "cv_folds": 5,
        "cv_best_f1": round(grid.best_score_, 4),
        "test_accuracy": round(acc, 4),
        "test_precision": round(prec, 4),
        "test_recall": round(rec, 4),
        "test_f1": round(f1, 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }
    (OUT_DIR / "sms_model_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    print(f"\nSaved: {OUT_DIR / 'sms_model.pkl'}")
    print(f"Saved: {OUT_DIR / 'vectorizer.pkl'}")
    print(f"Saved: {OUT_DIR / 'sms_model_meta.json'}")

    # ── Log to experiment tracker ───────────────────────────────────
    log_run(
        model_name="sms_detector",
        model_type="TF-IDF + LinearSVC (GridSearchCV)",
        hyperparams=grid.best_params_,
        cv_scores={"mean": round(grid.best_score_, 4)},
        test_scores={
            "accuracy": round(acc, 4),
            "f1": round(f1, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
        },
        dataset_path=str(RAW),
    )
    print("\n-- All experiment runs --")
    print_comparison()


if __name__ == "__main__":
    main()
