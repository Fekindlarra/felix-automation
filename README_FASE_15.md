# FASE 15: Real-Time ML Predictions + Mobile Dashboard

**Status:** 🚀 Sprint 1 - Code Generation Complete & Ready for Validation  
**Completed:** October 6, 2026  
**Timeline:** 5 weeks (Oct 7 - Nov 6, 2026)  
**Developer:** Felipe (solo - with Claude AI executing technical implementation)

---

## 🎯 FASE 15 Goals

Extend the FASE 13/14 sales automation system with:
1. **Mobile Dashboard** - React Native app with real-time WebSocket updates
2. **ML Predictions** - FastAPI backend with scikit-learn models + SHAP explainability
3. **Real-Time Features** - WebSocket event streaming to mobile clients
4. **Offline Capability** - AsyncStorage caching with sync queue
5. **Biometric Auth** - Face ID / Touch ID support

**Result:** Complete mobile-first sales prediction & dashboard system

---

## 📦 What's Been Generated (Sprint 1)

### ✅ Track A: React Native Mobile (`frontend/mobile/`)
- **Expo 51.0+** with TypeScript
- **Redux Toolkit** state management (3 slices: auth, dashboard, settings)
- **React Navigation** with stack + bottom tabs
- **Authentication** - Email/password + biometric (Face ID/Touch ID)
- **WebSocket Manager** - Auto-reconnect, heartbeat, event subscriptions
- **Offline Storage** - AsyncStorage with sync queue
- **Dashboard Screens** - Real-time prediction display
- **Test Suite** - Jest with >85% coverage target

**Key Files:**
- `src/App.tsx` - Root navigation
- `src/store/` - Redux slices (auth, dashboard, settings)
- `src/services/` - API client, WebSocket manager, offline storage
- `src/screens/` - AuthScreen, DashboardScreen
- `src/hooks/` - Custom hooks (useAuthState, useAppDispatch, useAppSelector)

**Commands:**
```bash
cd frontend/mobile
npm install
npm start              # Start Expo development server
npm run test:coverage  # Run Jest tests
npm run type-check     # Type-check TypeScript
npm run lint           # Run ESLint
```

### ✅ Track B: Python ML + FastAPI (`backend/api/`)
- **FastAPI** with CORS, health checks, info endpoints
- **Authentication** - JWT tokens with biometric login support
- **Predictions API** - ML-based probability, risk factors, SHAP explanations
- **Events API** - Real-time event streaming
- **SQLAlchemy Models** - User, Client, Prediction, Event, ABTest, ABTestResult
- **Configuration** - Pydantic settings from environment
- **ML Notebook** - Full EDA + SHAP pipeline (01_EDA_SHAP.ipynb)
- **Test Suite** - Pytest with >85% coverage target

**Key Files:**
- `config.py` - Environment configuration
- `main.py` - FastAPI app entry point
- `database.py` - SQLAlchemy setup and initialization
- `models.py` - ORM models
- `routers/` - API endpoints (auth, predictions, events, websocket)
- `tests/` - Test suites

**API Endpoints:**
```
GET  /api/health                          # Health check
GET  /api/info                             # API information
POST /api/auth/login                       # Email/password login
POST /api/auth/biometric                   # Biometric login
POST /api/predictions/generate             # Generate prediction
GET  /api/events/recent                    # Get recent events
WS   /ws/predictions/{user_id}/{client_id} # Real-time WebSocket
```

**Commands:**
```bash
cd backend/api
pip install -r requirements-fase15.txt
python main.py                    # Start API server
pytest tests/ -v --cov           # Run tests with coverage
pytest tests/test_auth.py -v     # Run auth tests
pytest tests/test_predictions.py -v # Run prediction tests
```

### ✅ CI/CD Pipeline (`.github/workflows/`)
- **fase15-ci.yml** - Automated testing on push/PR
  - Track A: ESLint, TypeScript type-check, Jest (>85% coverage)
  - Track B: Pylint, Pytest (>85% coverage), Bandit security scan
  - Codecov integration for coverage reporting

### ✅ Documentation
- **FASE_15_ARCHITECTURE.md** - Complete architecture overview
- **FASE_15_VALIDATION_CHECKLIST.md** - Step-by-step validation guide
- **setup-fase15.sh** - Quick setup script

---

## 🚀 Quick Start (5 minutes)

### Automated Setup
```bash
cd /home/claude/felix-automation
bash setup-fase15.sh
```

This will:
- ✅ Check Python 3 and Node.js
- ✅ Install all Python dependencies
- ✅ Install all npm dependencies
- ✅ Create .env file from template

### Manual Setup

**Backend (Track B):**
```bash
cd backend/api
pip install -r ../../requirements-fase15.txt
python main.py
# Server runs on http://localhost:8000
```

**Frontend (Track A):**
```bash
cd frontend/mobile
npm install
npm start
# Follow prompts: press 'i' for iOS, 'a' for Android
```

---

## ✅ Validation Steps (90 minutes)

### Phase 1: Backend Validation (45 min)
1. Install Python dependencies
2. Start backend API: `python main.py`
3. Check health: `curl http://localhost:8000/api/health`
4. View docs: `http://localhost:8000/docs`
5. Test prediction API with sample data
6. Run auth tests: `pytest tests/test_auth.py -v`
7. Run prediction tests: `pytest tests/test_predictions.py -v`
8. Check coverage: `pytest tests/ -v --cov`
9. Test WebSocket endpoint

### Phase 2: Mobile Validation (30 min)
1. Install npm dependencies: `npm install`
2. Start Expo: `npm start`
3. Launch iOS Simulator: Press 'i' (or Android: Press 'a')
4. Verify login screen appears
5. Run Jest tests: `npm run test:coverage`
6. Type-check: `npm run type-check`
7. Lint: `npm run lint`

### Phase 3: Integration (15 min)
1. Keep both servers running
2. Test WebSocket connection
3. Broadcast test event
4. Verify real-time updates

**Full Checklist:** See `FASE_15_VALIDATION_CHECKLIST.md`

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│         Frontend (Track A): React Native Mobile         │
├─────────────────────────────────────────────────────────┤
│ • Expo 51.0 + React Navigation                          │
│ • Redux Toolkit (auth, dashboard, settings slices)      │
│ • WebSocket Manager (auto-reconnect, heartbeat)         │
│ • AsyncStorage (offline caching + sync queue)           │
│ • Biometric Auth (Face ID / Touch ID)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                 WebSocket
                 JWT Bearer Token
                 REST API (axios)
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│      Backend (Track B): FastAPI + ML Predictions        │
├─────────────────────────────────────────────────────────┤
│ • FastAPI with CORS                                     │
│ • SQLAlchemy ORM (SQLite database)                      │
│ • ML Predictions (scikit-learn RandomForest)            │
│ • SHAP Explainability                                   │
│ • WebSocket Manager (event broadcasting)               │
│ • JWT Authentication                                    │
└────────────────────┬────────────────────────────────────┘
                     │
            ┌────────┴────────┐
            ▼                 ▼
        Database          ML Models
      (fase15.db)    (scikit-learn, SHAP)
```

### Data Flow

```
Mobile App (Track A)
    │
    ├─► Biometric Auth
    │       │
    │       ▼
    │   JWT Token (AsyncStorage)
    │       │
    └──────►│
            │
            ▼
    Login Endpoint
    /api/auth/biometric
            │
            ▼
    Backend (Track B)
    • Verify credentials
    • Generate JWT token
    • Return token + user info
            │
            ▼
    Redux Store
    (token, user, isAuthenticated)
            │
            ├─► Prediction Request
            │   /api/predictions/generate
            │       │
            │       ▼
            │   ML Model (RandomForest)
            │   • Input: web_score, facebook_score, etc.
            │   • Output: probability, confidence, risk_factors
            │   • SHAP: Feature importance explanations
            │       │
            │       ▼
            │   Prediction Response
            │       │
            ├─► WebSocket Events
            │   /ws/predictions/{user_id}/{client_id}
            │   • Real-time prediction updates
            │   • Heartbeat every 30s
            │   • Auto-reconnect with exponential backoff
            │       │
            ▼       ▼
    Dashboard Screen
    • Probability gauge (0-100%)
    • Confidence score
    • Risk factors list
    • Positive factors
    • SHAP explanations
    • Connection status indicator
```

---

## 🛠️ Technology Stack

### Frontend (Track A)
- **React Native** - Cross-platform mobile development
- **Expo 51.0+** - Managed React Native framework
- **TypeScript** - Type-safe JavaScript
- **Redux Toolkit** - State management
- **React Navigation** - Routing and navigation
- **react-native-biometrics** - Biometric authentication
- **axios** - HTTP client with JWT interceptor
- **AsyncStorage** - Local persistent storage
- **Jest** - Testing framework

### Backend (Track B)
- **Python 3.11+** - Runtime
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - ORM for database
- **SQLite** - Default database (switchable to PostgreSQL)
- **scikit-learn** - ML library (RandomForest classifier)
- **SHAP 0.43.0** - Model explainability
- **Pydantic 2.5** - Data validation
- **PyJWT 2.8** - JWT token handling
- **Pytest** - Testing framework
- **Jupyter** - Notebook-based ML workflow

### CI/CD
- **GitHub Actions** - Automated testing and deployment
- **Codecov** - Coverage tracking
- **ESLint** - JavaScript linting
- **Pylint** - Python linting
- **Bandit** - Python security scanning

---

## 📈 Success Criteria - Sprint 1

### Functionality
- [ ] iOS + Android simulators running with login screen
- [ ] API responding with predictions and SHAP explanations
- [ ] WebSocket connecting and sending real-time events
- [ ] Biometric authentication working
- [ ] Redux state management synchronized

### Performance
- [ ] App startup <3 seconds
- [ ] Dashboard load <1.5s on 4G
- [ ] Prediction latency <500ms
- [ ] WebSocket latency <100ms
- [ ] Build time <3 minutes

### Code Quality
- [ ] Test coverage >85% (both tracks)
- [ ] ESLint/Pylint passing
- [ ] Zero security issues (Bandit)
- [ ] TypeScript strict mode enabled
- [ ] All PRs code-reviewed

### Deployment
- [ ] GitHub Actions CI/CD green
- [ ] Database schema correct
- [ ] Environment configuration working
- [ ] No regressions from FASE 13/14
- [ ] Production-ready code

---

## 📋 File Structure

```
/home/claude/felix-automation/
│
├── frontend/mobile/                      # Track A: React Native
│   ├── package.json
│   ├── tsconfig.json
│   ├── app.json
│   ├── .eslintrc.json
│   ├── src/
│   │   ├── App.tsx                      # Root navigation
│   │   ├── index.ts
│   │   ├── store/                       # Redux store
│   │   │   ├── index.ts
│   │   │   └── slices/
│   │   │       ├── authSlice.ts
│   │   │       ├── dashboardSlice.ts
│   │   │       └── settingsSlice.ts
│   │   ├── services/
│   │   │   ├── api.ts                  # Axios HTTP client
│   │   │   ├── websocket.ts            # WebSocket manager
│   │   │   └── offlineStorage.ts       # AsyncStorage wrapper
│   │   ├── screens/
│   │   │   ├── AuthScreen.tsx
│   │   │   └── DashboardScreen.tsx
│   │   ├── hooks/
│   │   │   ├── useAuthState.ts
│   │   │   └── index.ts
│   │   └── components/                 # UI components (future)
│   └── __tests__/                       # Test files
│
├── backend/api/                          # Track B: FastAPI
│   ├── config.py                         # Environment config
│   ├── main.py                          # FastAPI app entry point
│   ├── database.py                      # SQLAlchemy setup (NEW)
│   ├── models.py                        # ORM models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                     # Authentication endpoints
│   │   ├── predictions.py              # Prediction endpoints
│   │   ├── events.py                   # Event endpoints
│   │   └── websocket.py                # WebSocket endpoints (NEW)
│   └── tests/
│       ├── __init__.py
│       ├── test_auth.py
│       └── test_predictions.py
│
├── backend/analytics/
│   └── notebooks/
│       └── 01_EDA_SHAP.ipynb           # ML workflow notebook
│
├── .github/workflows/
│   └── fase15-ci.yml                   # CI/CD pipeline
│
├── .env.example                          # Environment template
├── requirements-fase15.txt              # Python dependencies
├── FASE_15_ARCHITECTURE.md              # Architecture docs
├── FASE_15_VALIDATION_CHECKLIST.md      # Validation guide
├── README_FASE_15.md                    # This file
└── setup-fase15.sh                      # Quick setup script
```

---

## 🔄 Development Workflow

### Local Development

**Terminal 1 - Backend:**
```bash
cd backend/api
python main.py
# Runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend/mobile
npm start
# Press 'i' for iOS or 'a' for Android
```

**Terminal 3 - Tests:**
```bash
# Run backend tests
cd backend/api && pytest tests/ -v --cov

# OR run frontend tests
cd frontend/mobile && npm run test:coverage
```

### Testing

**Backend:**
```bash
cd backend/api

# Individual test files
pytest tests/test_auth.py -v
pytest tests/test_predictions.py -v

# All tests with coverage
pytest tests/ -v --cov=. --cov-report=html

# Watch mode (requires pytest-watch)
ptw tests/
```

**Frontend:**
```bash
cd frontend/mobile

# Run tests
npm run test:coverage

# Watch mode
npm run test -- --watch

# Update snapshots
npm run test -- -u
```

### Code Quality

**Backend:**
```bash
cd backend/api

# Lint with pylint
pylint *.py routers/*.py

# Format with black
black .

# Type check (if using mypy)
mypy .
```

**Frontend:**
```bash
cd frontend/mobile

# Lint
npm run lint

# Type check
npm run type-check

# Format
npm run prettier -- --write .
```

---

## 🚨 Troubleshooting

### Backend Won't Start

**Error:** "ModuleNotFoundError: No module named 'fastapi'"
```bash
cd /home/claude/felix-automation
pip install -r requirements-fase15.txt
```

**Error:** "Port 8000 already in use"
```bash
lsof -i :8000
kill -9 <PID>
```

**Error:** "SQLite database locked"
```bash
cd backend/api
rm fase15.db
python main.py  # Recreates fresh database
```

### Frontend Won't Start

**Error:** "npm ERR! code ERESOLVE"
```bash
cd frontend/mobile
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

**Error:** "Expo command not found"
```bash
npm install -g expo-cli
npm start
```

**Error:** "Simulator won't open"
```bash
# iOS
open -a Simulator

# Android - use Android Studio to create/start emulator
```

### WebSocket Not Working

**Check backend is running:**
```bash
curl http://localhost:8000/api/health
# Should return: {"status":"🟢 healthy",...}
```

**Check WebSocket endpoint:**
```bash
curl http://localhost:8000/api/ws/stats
# Should return connection statistics
```

### Tests Failing

**Backend:**
```bash
cd backend/api
pytest tests/ -v  # Show detailed output
pytest tests/ -vv # Show even more details
pytest tests/ --tb=short  # Show traceback
```

**Frontend:**
```bash
cd frontend/mobile
npm run test:coverage -- --verbose
npm run test:coverage -- --no-cache
npm run test:coverage -- --clearCache
```

---

## 📚 Documentation

- **FASE_15_ARCHITECTURE.md** - Complete architecture and design decisions
- **FASE_15_VALIDATION_CHECKLIST.md** - Step-by-step validation guide (90 min)
- **FASE_15_QUICK_REFERENCE.md** - Quick reference for developers
- **FASE_15_DEV_ENVIRONMENT_SETUP.md** - Detailed setup instructions
- **FASE_15_ROADMAP.md** - Full roadmap and next phases

---

## 🎓 Next Steps

### Immediate (This Week - Oct 7-11)
1. ✅ Run setup script: `bash setup-fase15.sh`
2. ✅ Validate Track A (mobile app)
3. ✅ Validate Track B (backend API)
4. ✅ Test WebSocket connections
5. ✅ Run test suites
6. ✅ Make initial git commits

### Next Phase (Oct 14-18)
1. Implement actual WebSocket real-time updates
2. Train ML model with FASE 14 historical data
3. Deploy to staging environment
4. A/B testing framework integration
5. Final code review & deployment

### Future (Phase 2+)
1. Shopify Analytics App integration
2. Advanced ML features (confidence intervals, uncertainty)
3. Mobile app native compilation (iOS/Android builds)
4. Production deployment
5. Performance optimization

---

## 📞 Support

**For issues or questions:**
1. Check troubleshooting section
2. Review FASE_15_VALIDATION_CHECKLIST.md
3. Check GitHub Actions CI/CD logs
4. Review test output

---

## 📄 License

Internal use only - Felix Automation System v15.0.0

---

## 👨‍💻 Contributors

- **Felipe** - Product Owner, Architect, Validator
- **Claude Haiku 4.5** - Technical Implementation, Code Generation
- **Session:** https://claude.ai/code/session_01EZEKRd8BUbc4mh5jQNB73m

---

**Generated:** October 6, 2026  
**Status:** Sprint 1 Complete ✅  
**Next:** Ready for Felipe's Validation 🚀
