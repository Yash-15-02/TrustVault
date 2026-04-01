# TrustVault AI

**Real-time fraud detection engine** that combines SMS scam analysis with transaction risk scoring to protect digital payments. Built with **FastAPI** + **scikit-learn** backend and **React Native** + **Expo** mobile app with professional animations and real-time analysis.

## 📱 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React Native, TypeScript, Expo 54, React Native Reanimated |
| **Backend** | FastAPI 0.135, Uvicorn, scikit-learn, pandas, numpy |
| **ML Models** | TF-IDF + LinearSVC (SMS), HistGradientBoosting + SMOTE (Transactions) |
| **Database** | SQLite (audit logs) |
| **UI/UX** | Animated components, gradient backgrounds, theme system (light/dark) |

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        React Native Expo App                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │ Home Screen     │  │ SMS Analysis     │  │ Transaction     │   │
│  │ - Navigation    │  │ - Text Input     │  │ Analysis        │   │
│  │ - Cards         │  │ - Animated Card  │  │ - Toggle Switch │   │
│  │ - Gradient BG   │  │ - Results        │  │ - 3 Numbers     │   │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘   │
│                              │                      │               │
│                              └──────────┬───────────┘               │
│                                         ▼                           │
│                        fetch (10s timeout)                          │
│                             X-Auth-Key                              │
└────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ POST /analyze
                                 ▼
          ┌──────────────────────────────────────────────┐
          │           FastAPI Server (0.0.0.0:8000)      │
          │                                              │
          │  ┌──────────┐     ┌────────────────────┐    │
          │  │ SMS      │     │ Transaction        │    │
          │  │ Detector │     │ Analyzer           │    │
          │  │ TF-IDF + │     │ SMOTE +            │    │
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
          └──────────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   JSON Response   /audit endpoint   /stats endpoint
```

## 🎯 Key Features

### Backend Features

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

### Mobile App Features

| Feature | Details |
|---|---|
| **Animated UI** | React Native Reanimated with spring animations, fade-in effects, slide-down transitions |
| **Tab Navigation** | Three-screen navigation: Home, SMS Analysis, Transaction Analysis |
| **SMS Analysis Screen** | Real-time SMS text input with instant API analysis and animated results display |
| **Transaction Analysis Screen** | 3 numeric fields + custom toggle switch for receiver status with fraud risk scoring |
| **Risk Visualization** | Color-coded risk badges (Green: Low, Orange: Medium, Red: High) with confidence scores |
| **Theme Support** | Professional light/dark mode with fintech color palette (blues, gradients) |
| **Gradient Backgrounds** | Beautiful purple-blue gradient (667EEA to 764BA2) with animation support |
| **Error Handling** | User-friendly error messages with timeout protection (10-second API deadline) |
| **Responsive Design** | Optimized for iOS and Android with TextInput visibility in both themes |
| **Type Safety** | Full TypeScript support with API response interfaces |

## 🚀 Quick Start

### Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Generate datasets (optional)
cd data\raw
python generate_datasets.py
cd ..\..\

# Train models (required on first run)
python training/train_sms_model.py
python training/train_transaction_model.py

# Run FastAPI server
$env:PYTHONPATH="c:\Users\ADMIN\Downloads\TrustVault\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Server starts at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### Frontend Setup (React Native + Expo)

```powershell
cd mobile-app
npm install

# Start Expo development server
npx expo start
```

**On first run**, update the backend URL in the app to match your local IP:
- Find your IP: `ipconfig` → Look for "IPv4 Address" (e.g., `192.168.1.4`)
- In [mobile-app/app/(tabs)/analyze-sms.tsx](mobile-app/app/(tabs)/analyze-sms.tsx) and [analyze-txn.tsx](mobile-app/app/(tabs)/analyze-txn.tsx)
- Change: `const API_URL = 'http://localhost:8000'` → `const API_URL = 'http://192.168.x.x:8000'`

Then:
- Press `i` for iOS simulator, `a` for Android emulator, or scan QR with **Expo Go** app on phone

### Configuration

Both backend and frontend can be customized:

**Backend** — Create `.env` file:
```env
DB_PATH=./audit.db
REQUIRE_AUTH=false
ALERT_WEBHOOK_URL=
```

**Frontend** — Update API endpoint as mentioned above

## 📊 Data & Training

### Generate Datasets
```powershell
cd backend/data/raw
python generate_datasets.py
```

For production-grade runs, replace with:
- `sms_spam.csv` from [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection)
- `creditcard.csv` from [Kaggle Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)

### Train Models
```powershell
cd backend
python training/train_sms_model.py
python training/train_transaction_model.py
```

Each training run:
- Performs **GridSearchCV** with **5-fold stratified cross-validation**
- Applies **SMOTE** oversampling (transaction model) for handling class imbalance
- Saves the best model + **metadata sidecar** (`*_meta.json`) with hyperparameters and scores
- Logs results to **experiment tracker** at `data/experiments/runs.json`

## 📚 API Reference

All API endpoints require the backend server to be running on port 8000.

### Endpoints

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

### Request Examples

#### SMS Analysis
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "message": "You have been charged Rs. 4000",
    "amount": 0.01,
    "is_new_receiver": 0,
    "transactions_today": 0
  }'
```

#### Transaction Analysis
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Payment processed",
    "amount": 75000,
    "is_new_receiver": 1,
    "transactions_today": 8
  }'
```

### Response Example

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

## 🧪 Testing

### Backend Tests
```powershell
cd backend
pytest tests/ -v
```

**Test Coverage:**
- **API Tests** (20 tests): Endpoint validation, error handling, request/response validation
- **Model Tests** (14 tests): SMS detector logic, transaction analyzer predictions
- **Feature Engineering** (18 tests): Feature computation, edge case handling

### Manual Testing with Mobile App
1. **Start backend server:**
   ```powershell
   cd backend
   $env:PYTHONPATH="c:\Users\ADMIN\Downloads\TrustVault\backend"
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Start mobile app:**
   ```powershell
   cd mobile-app
   npx expo start
   ```

3. **Test in Expo Go or Simulator:**
   - **Home Screen**: Verify navigation cards animate smoothly
   - **SMS Analysis**: Test with sample messages
     - Legitimate: "Your payment of Rs 500 has been successful"
     - Suspicious: "Verify your account at suspicious-link.com"
   - **Transaction Analysis**: Test with various amounts and settings
     - Low risk: Amount 1000, existing receiver, 1 transaction today
     - Medium risk: Amount 50000, new receiver, 3 transactions today
     - High risk: Amount 100000, new receiver, 8+ transactions today

## 📁 Project Structure

```
TrustVault/
├── backend/                                   # FastAPI server with ML models
│   ├── app/
│   │   ├── main.py                           # FastAPI app, startup events, observatory
│   │   ├── config.py                         # Configuration from .env
│   │   ├── schemas.py                        # Pydantic request/response models
│   │   ├── core/
│   │   │   ├── auth.py                       # Optional X-API-Key authentication
│   │   │   ├── database.py                   # SQLite audit logging
│   │   │   └── loader.py                     # ML model & vectorizer loader
│   │   ├── routes/
│   │   │   └── analyze.py                    # POST /analyze with timing & audit
│   │   ├── services/
│   │   │   ├── sms_service.py                # SMS detector (TF-IDF + LinearSVC)
│   │   │   └── txn_service.py                # Transaction analyzer (HistGradientBoosting)
│   │   ├── models/
│   │   │   ├── sms_detector.py               # SMS scam detection logic
│   │   │   └── transaction_analyzer.py       # Transaction fraud scoring
│   │   └── utils/
│   │       ├── alert.py                      # Pluggable alerting (file/console/webhook)
│   │       └── feature_engineering.py        # 8 derived fraud features
│   ├── training/
│   │   ├── train_sms_model.py                # SMS model training with GridSearchCV
│   │   ├── train_transaction_model.py        # Transaction model training with SMOTE
│   │   └── experiment_tracker.py             # JSON experiment logging & tracking
│   ├── data/
│   │   ├── raw/                              # Raw datasets (sms_spam.csv, creditcard.csv)
│   │   ├── processed/                        # Processed CSVs with engineered features
│   │   ├── trained_models/                   # Saved models (.pkl) + metadata (.json)
│   │   ├── experiments/                      # runs.json - training history
│   │   └── alerts/                           # alert_log.jsonl - audit trail
│   ├── tests/
│   │   ├── conftest.py                       # Pytest fixtures
│   │   ├── test_api.py                       # API endpoint tests (20 tests)
│   │   ├── test_models.py                    # ML model unit tests (14 tests)
│   │   └── test_feature_engineering.py       # Feature engineering tests (18 tests)
│   ├── requirements.txt
│   └── .env.example
│
├── mobile-app/                                # React Native Expo mobile app
│   ├── app/
│   │   ├── _layout.tsx                       # Root navigation setup
│   │   └── (tabs)/
│   │       ├── _layout.tsx                   # Tab navigation (Home, SMS, Transaction)
│   │       ├── index.tsx                     # Home screen with gradient background
│   │       ├── analyze-sms.tsx               # SMS fraud detection screen
│   │       └── analyze-txn.tsx               # Transaction fraud scoring screen
│   ├── components/
│   │   ├── animated-button.tsx               # Spring animation on press
│   │   ├── animated-card.tsx                 # Fade-in animation for results
│   │   ├── external-link.tsx
│   │   ├── haptic-tab.tsx                    # Haptic feedback for tabs
│   │   ├── hello-wave.tsx
│   │   ├── parallax-scroll-view.tsx
│   │   ├── themed-text.tsx                   # Theme-aware text component
│   │   ├── themed-view.tsx                   # Grid gradient background support
│   │   └── ui/
│   │       ├── collapsible.tsx               # Expandable section
│   │       └── icon-symbol.tsx               # Icon mapping system
│   ├── constants/
│   │   └── theme.ts                          # Colors, typography, fintech palette
│   ├── hooks/
│   │   ├── use-color-scheme.ts               # Light/dark mode detection
│   │   ├── use-color-scheme.web.ts           # Web color scheme support
│   │   └── use-theme-color.ts                # Theme-aware color retrieval
│   ├── types/
│   │   └── api.ts                            # TypeScript interfaces for API responses
│   ├── assets/
│   │   └── images/                           # Icons and images
│   ├── app.json                              # Expo config (app name, icon, splash)
│   ├── package.json                          # Dependencies & scripts
│   ├── tsconfig.json                         # TypeScript configuration
│   ├── eslint.config.js                      # ESLint rules
│   └── README.md                             # Mobile app documentation
│
└── .gitignore                                # Git ignore rules
```

## 🎨 UI/UX Features

### Color Scheme (Fintech Professional)
- **Primary**: `#007AFF` (Bright Blue)
- **Success**: `#34C759` (Green)
- **Warning**: `#FF9500` (Orange)
- **Error**: `#FF3B30` (Red)
- **Gradient**: Purple (`#667EEA`) → Blue (`#764BA2`)

### Animations
- **Button Press**: Spring animation with scale transform
- **Card Entrance**: Fade-in + slide-up effect
- **Screen Transitions**: Smooth tab navigation
- **Risk Badge**: Color transitions based on risk level

### Accessibility
- Color-coded risk indicators (not color-only)
- High contrast text for readability
- Haptic feedback on tab interactions
- Proper text sizing and spacing

## 🔧 Troubleshooting

### Backend Issues

**Port already in use:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000
# Kill process
taskkill /PID <PID> /F
```

**PYTHONPATH errors:**
```powershell
# Set PYTHONPATH before running
$env:PYTHONPATH="c:\Users\ADMIN\Downloads\TrustVault\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**ModuleNotFoundError:**
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Mobile App Issues

**Cannot connect to backend:**
- Verify backend is running: `http://localhost:8000/health`
- Check IP address: Run `ipconfig` and update API_URL in app code
- Ensure same network: Backend and phone must be on same Wi-Fi
- Check firewall: Windows firewall may block port 8000

**Text input not visible:**
- This is fixed in latest version. Update to latest code.

**"Text input is read-only" error:**
- Ensure `editable={true}` is set on TextInput components
- Check for conflicting styles

**Expo Won't Start:**
```powershell
# Clear cache and reinstall
cd mobile-app
rm -r node_modules
npm install
npx expo start --clear
```

## 📖 API Documentation

### Authentication (Optional)

If `REQUIRE_AUTH=true` in `.env`, include header:
```bash
curl -X POST http://localhost:8000/analyze \
  -H "X-API-Key: your-api-key" \
  ...
```

### Response Status Codes

- `200 OK`: Analysis successful
- `422 Unprocessable Entity`: Validation error (check request format)
- `401 Unauthorized`: Missing or invalid API key
- `500 Internal Server Error`: Server error (check logs)

### Rate Limiting

Currently no rate limiting. For production, configure in `config.py`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Open a pull request

## 📝 License

MIT License - free to use and modify

## 🔗 Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Native**: https://reactnative.dev/
- **Expo**: https://expo.dev/
- **scikit-learn**: https://scikit-learn.org/
- **GitHub Repository**: https://github.com/Yash-15-02/TrustVault

## 📧 Support

For issues, questions, or suggestions:
1. Check [existing GitHub issues](https://github.com/Yash-15-02/TrustVault/issues)
2. Create a new issue with detailed description
3. Include error messages, logs, and reproduction steps

---

**Built with ❤️ for secure digital payments**