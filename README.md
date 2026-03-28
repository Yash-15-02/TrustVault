# TrustVault AI

**Real-time fraud detection engine** that combines SMS scam analysis with transaction risk scoring to protect digital payments. Built with FastAPI, scikit-learn, and a production-oriented architecture.

## Architecture

```
                     ┌─────────────────────────────────────────────┐
                     │                FastAPI Server                │
                     │                                             │
  POST /analyze ────►│  ┌──────────┐     ┌────────────────────┐    │
                     │  │ SMS      │     │ Transaction        │    │
  X-API-Key ────────►│  │ Detector │     │ Analyzer           │    │
  (optional auth)    │  │ TF-IDF + │     │ SMOTE +            │    │
                     │  │ LinearSVC│     │ HistGradientBoost  │    │
                     │  └────┬─────┘     └────────┬───────────┘    │
                     │       │  SMS risk (40%)     │  Txn risk (60%)│
                     │       └────────┬────────────┘               │
                     │                ▼                             │
                     │       Combined Risk Score                   │
                     │       ┌──────────────┐                      │
                     │       │ Alert Engine │─── File JSONL log    │
                     │       │ (pluggable)  │─── Console log       │
                     │       │              │─── Webhook (HTTP)    │
                     │       └──────────────┘                      │
                     │                │                             │
                     │       ┌────────▼────────┐                   │
                     │       │  SQLite Audit   │                   │
                     │       │  Log Database   │                   │
                     │       └─────────────────┘                   │
                     └─────────────────────────────────────────────┘

  GET /audit ──────► Recent request history
  GET /stats ──────► Aggregate risk statistics
  GET /models/info ► Loaded model metadata & training scores
```

## Key Features

| Feature | Details |
|---|---|
| **SMS Scam Detection** | TF-IDF + LinearSVC with GridSearchCV hyperparameter tuning, 5-fold CV |
| **Transaction Fraud Scoring** | 8 engineered features, SMOTE for class imbalance, HistGradientBoosting with GridSearchCV |
| **Feature Engineering** | Derived features: `amount_log`, `velocity_flag`, `high_value_new_receiver`, `amount_per_txn` |
| **Experiment Tracking** | JSON-based run history with dataset hashing, score comparison tables |
| **Pluggable Alerts** | Console + file (JSONL) + HTTP webhook with deduplication |
| **Audit Database** | SQLite — every request logged with scores, response time, API key |
| **API Key Auth** | Optional `X-API-Key` header with named keys |
| **Observability** | `/audit`, `/stats`, `/models/info` endpoints |
| **Test Suite** | 40+ tests across API, model logic, and feature engineering |

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` → `.env` and customise if needed:

```powershell
copy .env.example .env
```

## Data

Generate training CSVs (no manual download required):

```powershell
cd data\raw
python generate_datasets.py
```

For research-grade runs, replace `sms_spam.csv` with the [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) and `creditcard.csv` with [Kaggle Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud), keeping the expected columns.

## Train Models

```powershell
cd backend
python training/train_sms_model.py
python training/train_transaction_model.py
```

Each training run:
- Runs **GridSearchCV** with **5-fold stratified cross-validation**
- Applies **SMOTE** oversampling (transaction model) for imbalanced fraud data
- Saves the best model + a **metadata sidecar** (`*_meta.json`) with scores and hyperparams
- Logs to the **experiment tracker** at `data/experiments/runs.json`

## Run API

```powershell
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service landing page |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive Swagger docs |
| `POST` | `/analyze` | Combined SMS + transaction risk scoring |
| `GET` | `/audit?limit=50` | Recent audit log entries |
| `GET` | `/stats` | Aggregated risk statistics |
| `GET` | `/models/info` | Loaded model metadata and training scores |
| `GET` | `/info` | JSON service metadata |

### POST /analyze — Example

```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 75000,
    "is_new_receiver": 1,
    "transactions_today": 8,
    "message": "URGENT: Your SBI account will be blocked. Verify at bit.ly/scam"
  }'
```

Response:

```json
{
  "risk_level": "High",
  "risk_score": 87,
  "recommendation": "BLOCK — Manual review required",
  "explanation": "SMS flagged as potential scam (confidence: 98.2%) ...",
  "alert": {
    "triggered": true,
    "type": "HIGH_RISK_TRANSACTION",
    "severity": "critical",
    "timestamp": "2026-03-28T15:30:00Z"
  },
  "delay_transaction": true,
  "sms_analysis": { "is_scam": true, "confidence": 98.2, "indicators": ["..."] },
  "transaction_analysis": { "risk_level": "High Risk", "fraud_probability": 0.82 },
  "response_time_ms": 12.34
}
```

## Run Tests

```powershell
cd backend
pytest tests/ -v
```

## Project Structure

```
TrustVault/
├── backend/
│   ├── app/
│   │   ├── main.py                        # FastAPI app, startup, observability endpoints
│   │   ├── config.py                      # All config from .env
│   │   ├── schemas.py                     # Pydantic request/response models
│   │   ├── core/
│   │   │   ├── auth.py                    # API key authentication (optional)
│   │   │   ├── database.py                # SQLite audit log
│   │   │   └── loader.py                  # Model loader with version checking
│   │   ├── routes/
│   │   │   └── analyze.py                 # POST /analyze with timing + audit
│   │   ├── services/
│   │   │   ├── sms_service.py             # SMS detector singleton
│   │   │   └── txn_service.py             # Transaction analyzer singleton
│   │   ├── models/
│   │   │   ├── sms_detector.py            # TF-IDF + SVC + indicator extraction
│   │   │   └── transaction_analyzer.py    # Enriched features + gradient boosting
│   │   └── utils/
│   │       ├── alert.py                   # Pluggable alerts (file/console/webhook)
│   │       └── feature_engineering.py     # 8 derived features for fraud detection
│   ├── training/
│   │   ├── train_sms_model.py             # GridSearchCV + 5-fold CV
│   │   ├── train_transaction_model.py     # SMOTE + GridSearchCV + 5-fold CV
│   │   └── experiment_tracker.py          # Lightweight JSON experiment logging
│   ├── data/
│   │   ├── raw/                           # sms_spam.csv, creditcard.csv
│   │   ├── processed/                     # Engineered features
│   │   ├── trained_models/                # *.pkl + *_meta.json (gitignored)
│   │   ├── experiments/                   # runs.json (training history)
│   │   └── alerts/                        # alert_log.jsonl
│   ├── tests/
│   │   ├── conftest.py                    # Shared fixtures
│   │   ├── test_api.py                    # API endpoint tests (20 tests)
│   │   ├── test_models.py                 # Model logic unit tests (14 tests)
│   │   └── test_feature_engineering.py    # Feature computation tests (18 tests)
│   ├── requirements.txt
│   └── .env.example
├── mobile-app/README.md
└── .gitignore

