# FASE 15: Architecture Overview

**Status:** Sprint 1 Code Generation Complete ✅  
**Generated:** October 6, 2026  
**Phase:** Ready for Validation & Testing

---

## 📦 What's Been Generated

### Track A: React Native Mobile (`frontend/mobile/`)
- ✅ **Expo 51.0+ scaffold** with TypeScript configuration
- ✅ **Redux Toolkit state management** (auth, dashboard, settings slices)
- ✅ **React Navigation** (stack + bottom tabs)
- ✅ **Authentication** (Email/Password + Biometric with react-native-biometrics)
- ✅ **WebSocket client** (auto-reconnect, heartbeat, event subscriptions)
- ✅ **Offline storage** (AsyncStorage caching + sync queue)
- ✅ **Dashboard screens** (real-time prediction display, connection status)
- ✅ **ESLint + Prettier** (code quality)
- ✅ **Jest** (unit tests, >85% coverage target)

**Key Files:**
- `package.json` - Dependencies (Expo, Redux, React Navigation, axios)
- `src/App.tsx` - Root navigation
- `src/store/` - Redux slices
- `src/services/` - API, WebSocket, offline storage
- `src/screens/` - AuthScreen, DashboardScreen
- `src/hooks/` - Custom hooks for auth state

**Dev Setup:**
```bash
cd frontend/mobile
npm install
npm start  # Press i for iOS, a for Android
```

---

### Track B: Python ML + FastAPI (`backend/api/`)
- ✅ **FastAPI app** with CORS, health checks, info endpoints
- ✅ **Authentication routes** (JWT tokens, biometric login)
- ✅ **Predictions API** (ML-based probability, risk factors, SHAP explanations)
- ✅ **Events API** (real-time event streaming, statistics)
- ✅ **SQLAlchemy models** (User, Client, Prediction, Event, ABTest, ABTestResult)
- ✅ **Configuration management** (pydantic-settings from .env)
- ✅ **ML Notebook** (01_EDA_SHAP.ipynb - full ML pipeline)

**Key Files:**
- `backend/api/main.py` - FastAPI app entry point
- `backend/api/config.py` - Settings from environment
- `backend/api/models.py` - Database models
- `backend/api/routers/` - API endpoints (auth, predictions, events)
- `backend/analytics/notebooks/01_EDA_SHAP.ipynb` - ML workflow

**Dev Setup:**
```bash
pip install -r requirements-fase15.txt
cd backend/api
python main.py  # Runs on http://localhost:8000
```

**API Documentation:**
- Health: `GET /api/health`
- Info: `GET /api/info`
- Login: `POST /api/auth/login`
- Predict: `POST /api/predictions/generate`
- Events: `GET /api/events/recent`

---

### CI/CD Pipeline (`.github/workflows/`)
- ✅ **fase15-ci.yml** - Automated testing on push/PR
  - Track A: npm lint, type-check, jest (>85% coverage)
  - Track B: pylint, pytest (>85% coverage), bandit security scan
  - Build checks for both platforms
  - Codecov integration for coverage reporting

---

## 🎯 Architecture Decisions

### Track A: React Native + Expo
**Why:** Fastest path to iOS + Android with shared codebase
- Expo handles tooling (no Xcode/Android Studio setup needed)
- Over-the-air updates
- Rich ecosystem of native modules
- TypeScript for type safety

**State Management:** Redux Toolkit
- auth: JWT token, user info, login state
- dashboard: Real-time WebSocket events
- settings: App preferences, offline mode toggle

**Networking:**
- REST API via axios (with JWT interceptor)
- WebSocket for real-time predictions
- AsyncStorage for offline cache

### Track B: Python ML + FastAPI
**Why:** Production-ready Python ML ecosystem
- scikit-learn RandomForest (>70% accuracy target)
- SHAP for model explainability
- FastAPI for async API endpoints
- Alembic for database migrations

**Model Pipeline:**
1. EDA in Jupyter (01_EDA_SHAP.ipynb)
2. Feature engineering (averages, variance, dummies)
3. RandomForest training (100 trees, max_depth=10)
4. SHAP values for each prediction
5. API endpoint returns: probability, confidence, factors, SHAP explanations

**Database:**
- SQLite default (can switch to PostgreSQL)
- SQLAlchemy ORM for type-safe queries
- Models for: Users, Clients, Predictions, Events, A/B Tests

---

## 🚀 Next Steps (For Felipe)

### Week 1 (Oct 7-11):
1. **Validate Track A (30 min):**
   ```bash
   cd frontend/mobile
   npm install
   npm start
   # Press i for iOS simulator - should launch app with login screen
   ```

2. **Validate Track B (45 min):**
   ```bash
   pip install -r requirements-fase15.txt
   cd backend/api
   python main.py
   # Visit http://localhost:8000/api/info - should show API info
   # Visit http://localhost:8000/docs - OpenAPI docs
   ```

3. **Test API (15 min):**
   ```bash
   curl -X POST http://localhost:8000/api/predictions/generate \
     -H "Content-Type: application/json" \
     -d '{
       "client_id": "test_001",
       "web_score": 75,
       "facebook_score": 85,
       "google_score": 80,
       "business_type": "ecommerce",
       "company_size": "pyme"
     }'
   ```

4. **Run Tests:**
   ```bash
   # Track A
   cd frontend/mobile && npm run test:coverage
   
   # Track B
   cd backend/api && pytest tests/ -v --cov
   ```

### Week 2 (Oct 14-18):
1. Implement WebSocket connection in Track A screens
2. Train ML model with actual FASE 14 data
3. Deploy to staging environment
4. A/B testing framework integration
5. Final code review & deployment to production

---

## 📊 Success Criteria - Sprint 1

### Functionality
- [ ] iOS + Android simulators running (Track A)
- [ ] API responding with predictions (Track B)
- [ ] SHAP explanations working
- [ ] WebSocket connecting and sending events
- [ ] ML model accuracy >70%

### Performance
- [ ] App startup <3s
- [ ] Dashboard load <1.5s (4G simulation)
- [ ] Prediction latency <500ms
- [ ] Build time <3min (React Native)

### Code Quality
- [ ] Test coverage >85%
- [ ] ESLint/pylint passing
- [ ] Zero security issues (bandit)
- [ ] All PRs code-reviewed

### Deployment
- [ ] GitHub Actions CI/CD green on all PRs
- [ ] Staging environment working
- [ ] Production rollout checklist ready

---

## 📞 Debugging Guide

### Track A Issues
- **"expo-cli not found"**: `npm install -g expo-cli`
- **"Simulator won't start"**: Ensure Xcode/Android Studio installed
- **"TypeScript errors"**: Run `npm run type-check` and fix
- **"Redux not found"**: Verify `npm install` completed

### Track B Issues
- **"ModuleNotFoundError"**: Run `pip install -r requirements-fase15.txt`
- **"SQLite database locked"**: Delete `fase15.db` and restart
- **"Port 8000 in use"**: `lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9`
- **"ML model not found"**: Run notebooks first to train models

---

## 🔗 Related Documents

- `FASE_15_ROADMAP.md` - Strategic vision & architecture
- `FASE_15_SPRINT_1_PLANNING.md` - Week-by-week breakdown
- `FASE_15_DEV_ENVIRONMENT_SETUP.md` - Detailed dev setup
- `FASE_15_INITIAL_TICKETS_BACKLOG.md` - Detailed tickets
- `FASE_15_QUICK_REFERENCE.md` - Developer quick reference

---

**Generated by:** Claude Haiku 4.5  
**Session:** https://claude.ai/code/session_01EZEKRd8BUbc4mh5jQNB73m  
**Next Update:** October 7, 2026 (After Sprint 1 Kickoff)
