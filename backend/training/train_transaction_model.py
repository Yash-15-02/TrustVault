"""
Train transaction fraud model on enriched features.

Pipeline: SMOTE oversampling → HistGradientBoosting with GridSearchCV
          + stratified 5-fold cross-validation.

Run:  cd backend && python training/train_transaction_model.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.utils.feature_engineering import FEATURE_COLUMNS, process_training_data  # noqa: E402
from training.experiment_tracker import log_run, print_comparison  # noqa: E402

RAW = BACKEND / "data" / "raw" / "creditcard.csv"
PROC = BACKEND / "data" / "processed" / "txn_engineered.csv"
OUT_DIR = BACKEND / "data" / "trained_models"


def main():
    if not RAW.exists():
        print(f"Missing {RAW}")
        print("Generate it:  python data/raw/generate_datasets.py")
        sys.exit(1)

    data = pd.read_csv(RAW)
    need = {"Amount", "V1", "V2", "Class"}
    if not need.issubset(set(data.columns)):
        print(f"Expected columns including: {sorted(need)}")
        sys.exit(1)

    # ── Feature engineering ─────────────────────────────────────────
    eng = process_training_data(data)
    PROC.parent.mkdir(parents=True, exist_ok=True)
    eng.to_csv(PROC, index=False)
    print(f"Engineered {len(eng)} rows -> {PROC}")
    print(f"Features: {FEATURE_COLUMNS}")
    print(f"Fraud rate: {eng['Class'].mean():.2%}")

    X = eng[FEATURE_COLUMNS]
    y = eng["Class"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    # ── SMOTE + model pipeline with Grid Search ─────────────────────
    pipeline = ImbPipeline([
        ("smote", SMOTE(random_state=42)),
        ("clf", HistGradientBoostingClassifier(
            random_state=42,
            class_weight="balanced",
        )),
    ])

    param_grid = {
        "smote__k_neighbors": [3, 5],
        "clf__max_depth": [5, 8, 12],
        "clf__learning_rate": [0.05, 0.08, 0.12],
        "clf__max_iter": [200, 400],
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    print("\nRunning GridSearchCV (5-fold) …")
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

    proba = best.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    f1 = f1_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    acc = (y_pred == y_test).mean()

    print(f"\n=== Test Results ===")
    print(f"ROC-AUC   : {auc:.4f}")
    print(f"Accuracy  : {acc:.4f}")
    print(f"Precision : {prec:.4f}")
    print(f"Recall    : {rec:.4f}")
    print(f"F1        : {f1:.4f}")
    print(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))

    # ── Save the classifier only (SMOTE not needed at inference) ────
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    final_clf = best.named_steps["clf"]
    joblib.dump(final_clf, OUT_DIR / "transaction_model.pkl")

    # ── Save metadata sidecar ───────────────────────────────────────
    meta = {
        "model_name": "transaction_analyzer",
        "model_type": "SMOTE + HistGradientBoosting (GridSearchCV)",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "best_params": {k: v for k, v in grid.best_params_.items()},
        "cv_folds": 5,
        "cv_best_f1": round(grid.best_score_, 4),
        "test_roc_auc": round(auc, 4),
        "test_accuracy": round(float(acc), 4),
        "test_precision": round(prec, 4),
        "test_recall": round(rec, 4),
        "test_f1": round(f1, 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_columns": FEATURE_COLUMNS,
        "fraud_rate": round(float(y.mean()), 4),
    }
    (OUT_DIR / "transaction_model_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    print(f"\nSaved: {OUT_DIR / 'transaction_model.pkl'}")
    print(f"Saved: {OUT_DIR / 'transaction_model_meta.json'}")

    # ── Log to experiment tracker ───────────────────────────────────
    log_run(
        model_name="transaction_analyzer",
        model_type="SMOTE + HistGradientBoosting (GridSearchCV)",
        hyperparams=grid.best_params_,
        cv_scores={"mean": round(grid.best_score_, 4)},
        test_scores={
            "accuracy": round(float(acc), 4),
            "f1": round(f1, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "roc_auc": round(auc, 4),
        },
        dataset_path=str(RAW),
    )
    print("\n-- All experiment runs --")
    print_comparison()


if __name__ == "__main__":
    main()
