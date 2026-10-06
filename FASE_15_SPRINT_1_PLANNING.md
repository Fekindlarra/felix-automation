# FASE 15 - Sprint 1 Planning & Execution

**Planning Date:** 2026-10-06 (Post FASE 14 Deployment)  
**Sprint Duration:** 2 weeks (Oct 7-20, 2026)  
**Sprint Goal:** Foundation & Infrastructure Setup for both Mobile Apps and Advanced Predictions  
**Status:** 🎯 READY FOR IMPLEMENTATION

---

## Executive Summary

**FASE 15** runs two parallel development tracks concurrently to maximize efficiency and revenue impact:

| Track | Focus | Team Size | Timeline | Revenue Target |
|-------|-------|-----------|----------|----------------|
| **15A** | React Native Mobile Apps (iOS/Android) | 4 people | 5 weeks | +$75K MRR |
| **15B** | ML-Based Predictions Engine | 4 people | 5 weeks | +$45K MRR |
| **TOTAL** | Real-Time Mobile + Predictive AI | 8 people | 5 weeks (parallel) | **+$120K MRR** |

Sprint 1 focuses on **architecture, setup, and proof-of-concept** for both tracks to de-risk the remaining sprints.

---

## Sprint 1: Week-by-Week Breakdown

### WEEK 1 (Oct 7-11, 2026)

#### ✅ TRACK A: Mobile Apps - Architecture & Setup

**Mon-Tue (Oct 7-8):**
- [ ] React Native project scaffold (Expo or bare React Native)
  - Choose: Expo (faster, limited customization) vs bare RN (full control)
  - Recommendation: **Expo + EAS Build** (simplifies App Store/Play Store builds)
- [ ] Project structure setup
  ```
  mobile/
  ├── app/                    # Expo app config
  ├── src/
  │   ├── components/         # Reusable UI components
  │   ├── screens/            # Screen implementations
  │   ├── navigation/         # React Navigation setup
  │   ├── redux/              # Redux state management
  │   ├── services/           # API + WebSocket clients
  │   ├── hooks/              # Custom React hooks
  │   └── utils/              # Helpers + constants
  ├── __tests__/              # Test suite
  ├── app.json                # Expo config
  ├── tsconfig.json           # TypeScript (recommended)
  ├── package.json
  └── eas.json                # EAS Build config
  ```
- [ ] TypeScript configuration (strong typing for mobile)
- [ ] ESLint + Prettier setup
- [ ] Repository structure (git branch `feat/mobile-track-a`)

**Wed (Oct 9):**
- [ ] Authentication system architecture decision
  - [ ] Biometric options: `react-native-biometrics` (iOS Keychain + Android BiometricPrompt)
  - [ ] Password fallback: `react-native-keychain` secure storage
  - [ ] JWT refresh token handling for session management
  - [ ] Mock auth service for early testing
- [ ] Create AuthContext + useAuth hook
- [ ] Build LoginScreen (form + biometric button)
- [ ] Create secure token storage layer

**Thu-Fri (Oct 10-11):**
- [ ] Redux state management setup
  - [ ] Redux Toolkit (simplified Redux API)
  - [ ] Slices: auth, dashboard, predictions, ui
  - [ ] Middleware: logger, error handler
- [ ] React Navigation setup
  - [ ] Stack Navigator (login flow)
  - [ ] Bottom Tab Navigator (main app)
  - [ ] Authentication check logic
- [ ] Base screen components
  - [ ] LoginScreen (stub)
  - [ ] DashboardScreen (empty)
  - [ ] PredictionsScreen (empty)
  - [ ] SettingsScreen (empty)

**Deliverables (Week 1A):**
- ✅ React Native project running on iOS + Android simulators
- ✅ Login/Auth flow working with mock data
- ✅ Navigation structure in place
- ✅ Redux store ready for data
- ✅ Git branch `feat/mobile-track-a` pushed with initial scaffold

---

#### ✅ TRACK B: Advanced Predictions - Data Pipeline Setup

**Mon-Tue (Oct 7-8):**
- [ ] Data preparation environment
  - [ ] Jupyter notebook for exploratory data analysis (EDA)
  - [ ] pandas + numpy for data wrangling
  - [ ] Load FASE 14 historical predictions (5,432 records)
  - [ ] Load actual outcomes from CRM integration (if available)
  - [ ] Data quality assessment: missing values, outliers, distribution
- [ ] Feature engineering planning
  - [ ] Identify client attributes → ML features (company size, industry, budget, etc.)
  - [ ] Create feature matrix (clients × features)
  - [ ] Normalize/scale features (StandardScaler)
  - [ ] Handle categorical variables (one-hot encoding)

**Wed (Oct 9):**
- [ ] ML model architecture decision
  - [ ] Model choice: **scikit-learn RandomForestClassifier** (recommended for tabular data)
  - [ ] Not using TensorFlow/Keras (overkill for this data; scikit-learn sufficient)
  - [ ] Train/test split: 80-20 (4,346 train / 1,086 test)
  - [ ] Cross-validation: 5-fold CV for robustness
  - [ ] Hyperparameter tuning: GridSearchCV for optimal params
- [ ] Create ML pipeline module
  ```python
  # backend/analytics/ml_pipeline.py
  class ConversionPredictionPipeline:
      def __init__(self):
          self.preprocessor = ColumnTransformer(...)
          self.model = RandomForestClassifier(...)
      
      def train(self, X, y):
          """Train model on historical data"""
      
      def predict(self, X):
          """Generate predictions for new clients"""
      
      def explain(self, X, prediction):
          """SHAP explanation for prediction"""
  ```
- [ ] Set up SHAP for explainability
  - [ ] Feature importance calculation
  - [ ] Individual prediction explanation (SHAP values)
  - [ ] Force plot visualization prep

**Thu-Fri (Oct 10-11):**
- [ ] Model training & validation
  - [ ] Train RandomForest on historical data
  - [ ] Cross-validation scoring (target: >70% accuracy)
  - [ ] Confusion matrix analysis (true positives, false positives)
  - [ ] ROC-AUC score calculation
  - [ ] Feature importance extraction (top 10 features)
- [ ] Save trained model
  - [ ] Pickle model to disk (`models/conversion_predictor_v1.pkl`)
  - [ ] Save preprocessing transformer
  - [ ] Create model loading utility
- [ ] Database schema updates
  - [ ] Prediction history table (track all predictions)
  - [ ] Model metadata table (model version, accuracy, date trained)
  - [ ] Indexes on prediction_history (client_id, timestamp)

**Deliverables (Week 1B):**
- ✅ ML model trained and saved locally
- ✅ Model accuracy >70% on test set
- ✅ SHAP integration ready for explainability
- ✅ Database schema updated with prediction_history table
- ✅ Git branch `feat/predictions-track-b` pushed with pipeline code

---

### WEEK 2 (Oct 14-18, 2026)

#### ✅ TRACK A: Mobile Apps - WebSocket & Real-Time Integration

**Mon-Tue (Oct 14-15):**
- [ ] WebSocket client for React Native
  - [ ] Library choice: `react-native-websocket` or native WebSocket API
  - [ ] Create WebSocketService singleton
  - [ ] Auto-reconnection logic with exponential backoff
  - [ ] HeartBeat (ping/pong) for mobile networks
- [ ] Real-time dashboard data flow
  - [ ] Subscribe to WebSocket events (prediction:generated, test:started)
  - [ ] Redux dispatch for incoming events
  - [ ] Update dashboard state in real-time
- [ ] Redux middleware for WebSocket
  - [ ] Thunk middleware: connect/disconnect actions
  - [ ] Event handler: broadcast event → redux dispatch
  - [ ] Error handling: connection failures, reconnection

**Wed (Oct 16):**
- [ ] DashboardScreen implementation (Part 1)
  - [ ] Real-time metrics cards (probability gauge, confidence indicator)
  - [ ] Prediction timeline visualization
  - [ ] WebSocket connection status indicator
  - [ ] Mock data for preview (until backend ready)
- [ ] Gauges & Charts for mobile
  - [ ] Probability gauge: circular dial (0-100%)
  - [ ] Confidence indicator: colored bar
  - [ ] Risk factors list: collapsible section
  - [ ] Positive factors list: expandable section

**Thu-Fri (Oct 17-18):**
- [ ] Offline capability with AsyncStorage
  - [ ] Cache dashboard data locally
  - [ ] Service Worker pattern for React Native (expo-sqlite + AsyncStorage)
  - [ ] Sync queue: queue actions when offline, sync when reconnected
  - [ ] Mock data fallback when offline
- [ ] Performance optimization (mobile-critical)
  - [ ] Lazy load charts (don't render until visible)
  - [ ] Virtualize long lists (PredictionsScreen)
  - [ ] Memoize expensive computations
  - [ ] Profiling: FPS should stay >50 on 4G network

**Deliverables (Week 2A):**
- ✅ DashboardScreen showing real-time predictions
- ✅ WebSocket connection working (mock data)
- ✅ Offline capability tested
- ✅ Performance benchmarks: <1.5s load on 4G
- ✅ Prototype ready for stakeholder preview

---

#### ✅ TRACK B: Advanced Predictions - API & Dashboard Integration

**Mon-Tue (Oct 14-15):**
- [ ] FastAPI endpoint for predictions
  - [ ] `POST /api/predictions/generate` - Generate prediction for client
  - [ ] Input: client_id, client attributes
  - [ ] Output: probability, confidence, risk_factors, positive_factors
  - [ ] Load trained model, run inference, return results
- [ ] Batch prediction job
  - [ ] Scheduled task: daily or weekly bulk predictions
  - [ ] APScheduler job: run every night at 2am
  - [ ] Process all clients in batches (100 at a time)
  - [ ] Store predictions in prediction_history table
  - [ ] Calculate accuracy vs actual outcomes

**Wed (Oct 16):**
- [ ] Explainability API endpoints
  - [ ] `GET /api/predictions/{id}/explanation` - SHAP values for prediction
  - [ ] Feature importance visualization JSON
  - [ ] "Why is this 72%?" interactive breakdown
  - [ ] Factor contribution calculation
- [ ] SHAP value calculation & storage
  - [ ] For each prediction, calculate SHAP values
  - [ ] Store top 5 positive factors + top 5 negative factors
  - [ ] Format for frontend visualization

**Thu-Fri (Oct 17-18):**
- [ ] Dashboard integration
  - [ ] Add Explainability Widget to internal_dashboard.html
  - [ ] Feature importance bar chart (SHAP values)
  - [ ] Factor contribution breakdown (why is prediction 72%?)
  - [ ] Historical accuracy tracker (predictions vs outcomes)
  - [ ] Model metadata display (version, trained date, accuracy)
- [ ] A/B Test: ML vs Rule-Based
  - [ ] Randomly assign 50% to new ML model, 50% to existing rule-based
  - [ ] Track both versions for comparison
  - [ ] Statistical significance test (chi-square)
  - [ ] Winner determination logic (if p-value < 0.05)

**Deliverables (Week 2B):**
- ✅ Predictions API working end-to-end
- ✅ Explainability dashboard showing SHAP values
- ✅ Batch prediction job running (test run completed)
- ✅ A/B test framework ready
- ✅ Accuracy vs actual outcomes tracking enabled

---

## Git Branching Strategy

### Branch Structure
```
production/
  ├── main (v14.0.0 - current production)
  └── stage (staging for testing)

development/
  ├── develop (integration branch for FASE 15)
  │
  ├── feat/mobile-track-a (Track A: Mobile Apps)
  │   ├── feat/mobile-auth
  │   ├── feat/mobile-dashboard
  │   ├── feat/mobile-websocket
  │   └── feat/mobile-offline
  │
  └── feat/predictions-track-b (Track B: Advanced Predictions)
      ├── feat/ml-pipeline
      ├── feat/ml-explainability
      ├── feat/ml-api
      └── feat/ml-abtesting
```

### Workflow
```
1. Developer creates feature branch from develop
   git checkout develop
   git pull origin develop
   git checkout -b feat/mobile-auth

2. Develop & commit
   git commit -m "feat: Add biometric authentication"

3. Push to remote
   git push origin feat/mobile-auth

4. Create Pull Request (Track Lead reviews)
   - Code review: 2+ reviewers
   - CI/CD checks: tests pass, coverage >85%
   - Approval: merge to develop

5. Merge to develop
   git merge feat/mobile-auth
   
6. Weekly integration
   - Thursday: merge develop → stage
   - Friday: test in staging
   - Monday: merge stage → production (or hold for gate)
```

---

## Development Environment Setup

### Local Setup (Each Developer)

**1. Clone & Setup**
```bash
git clone https://github.com/enbuenamesa/felix-automation.git
cd felix-automation

# Install Python dependencies (backend)
python3.11 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Install Node dependencies (mobile + frontend)
cd mobile
npm install --registry https://registry.npmjs.org/

# Or use Expo
npm install -g eas-cli
cd mobile
eas init  # Initialize EAS project
```

**2. Environment Variables**
```bash
# .env file (root)
ENVIRONMENT=development
DATABASE_URL=sqlite:///felix_dev.db
SECRET_KEY=your-dev-secret-key-here
SHOPIFY_API_KEY=mock-key-dev
SHOPIFY_API_SECRET=mock-secret-dev
REDIS_URL=redis://localhost:6379
SENDGRID_API_KEY=mock-key-dev

# mobile/.env (mobile app)
BACKEND_URL=http://localhost:8000
WEBSOCKET_URL=ws://localhost:8000
API_VERSION=v14
```

**3. Database Setup**
```bash
# Reset database for development
python backend/init_database.py --reset

# Run migrations (if any)
python -m alembic upgrade head
```

**4. Run Services Locally**

**Backend (FastAPI):**
```bash
cd backend
uvicorn main:app --reload --port 8000
# API available at http://localhost:8000
# WebSocket at ws://localhost:8000/ws
```

**Mobile App (Expo):**
```bash
cd mobile
npm start
# iOS: press 'i' → simulator opens
# Android: press 'a' → emulator opens
# or scan QR code with Expo Go app
```

**Frontend (Static files served by FastAPI):**
```bash
# Access at http://localhost:8000/internal_dashboard.html
# or http://localhost:8000/client_portal.html
```

### CI/CD Pipeline (GitHub Actions)

**On every push:**
- [ ] Run unit tests (pytest backend, jest mobile)
- [ ] Lint & format check (pylint, eslint)
- [ ] Coverage report (>85% target)
- [ ] Build mobile app (EAS build dry-run)
- [ ] Build backend (Docker image)

**On PR to develop:**
- [ ] All above + code review gate
- [ ] Security scan (bandit)
- [ ] Dependency check

**On merge to develop:**
- [ ] Build & push Docker image to staging registry
- [ ] Deploy to staging environment
- [ ] Run integration tests in staging
- [ ] Notify team: staging deployment complete

---

## Technology Stack Finalization

### Track A: Mobile Apps

| Layer | Choice | Version | Notes |
|-------|--------|---------|-------|
| **Framework** | React Native + Expo | 51.0+ | Fast iteration, easy App Store deployment |
| **Language** | TypeScript | 5.3+ | Type safety, better DX |
| **Navigation** | React Navigation | 6.x | Standard in React Native |
| **State Mgmt** | Redux Toolkit | 1.9+ | Simplified Redux API |
| **Async Storage** | AsyncStorage | 1.21+ | Local data persistence |
| **WebSocket** | Native WebSocket API | Built-in | No additional dependency |
| **Biometric** | react-native-biometrics | 6.0+ | iOS Keychain + Android BiometricPrompt |
| **Keychain** | react-native-keychain | 9.x | Secure credential storage |
| **Charts** | react-native-svg + d3 | - | Lightweight, performant |
| **Testing** | Jest + React Native Testing Library | - | Unit + integration tests |
| **Build** | EAS Build | - | Managed build service (iOS + Android) |
| **App Store** | App Store + Google Play | - | Distribution channels |

### Track B: Advanced Predictions

| Layer | Choice | Version | Notes |
|-------|--------|---------|-------|
| **ML Framework** | scikit-learn | 1.3+ | Production-ready, no training overhead |
| **Model** | RandomForestClassifier | - | Excellent for tabular data, interpretable |
| **Explainability** | SHAP | 0.43+ | Feature importance + SHAP values |
| **Data Processing** | pandas + numpy | Latest | Standard data manipulation |
| **Preprocessing** | scikit-learn Pipeline | - | ColumnTransformer + StandardScaler |
| **Visualization** | plotly + matplotlib | - | Interactive + static charts |
| **Database** | SQLite (FASE 14) | - | prediction_history table |
| **Async Jobs** | APScheduler | 3.10+ | Scheduled batch predictions |
| **API** | FastAPI (existing) | 0.104+ | RESTful endpoints |
| **Testing** | pytest + pytest-cov | - | Unit + integration tests |

---

## Initial Ticket List - TRACK A (Mobile Apps)

### Tier 1: Foundation (Week 1-2)
1. **[15A-001]** Setup React Native project scaffold (Expo)
   - Assignee: Lead Mobile Dev
   - Effort: 1d
   - Depends: None
   - Status: Ready to start

2. **[15A-002]** Implement authentication system (biometric + password)
   - Assignee: Mobile Dev 2
   - Effort: 2d
   - Depends: 15A-001
   - Includes: LoginScreen, biometric prompt, token storage

3. **[15A-003]** Setup Redux state management
   - Assignee: Lead Mobile Dev
   - Effort: 1d
   - Depends: 15A-001
   - Includes: Slices (auth, dashboard, predictions)

4. **[15A-004]** Implement React Navigation
   - Assignee: Mobile Dev 2
   - Effort: 1d
   - Depends: 15A-001, 15A-003

5. **[15A-005]** Create WebSocket client service
   - Assignee: Lead Mobile Dev
   - Effort: 1.5d
   - Depends: 15A-001
   - Includes: Auto-reconnect, heartbeat

6. **[15A-006]** Build DashboardScreen (real-time predictions)
   - Assignee: Mobile Dev 2
   - Effort: 2d
   - Depends: 15A-003, 15A-005
   - Includes: Gauges, charts, widgets

7. **[15A-007]** Implement offline capability (AsyncStorage + sync queue)
   - Assignee: Lead Mobile Dev
   - Effort: 1.5d
   - Depends: 15A-003
   - Includes: Local caching, sync on reconnect

8. **[15A-008]** Performance optimization & profiling
   - Assignee: Mobile Dev 2
   - Effort: 1d
   - Depends: 15A-006
   - Target: <1.5s load on 4G

### Tier 2: Polish (Week 3-4)
9. **[15A-009]** Build PredictionsScreen with detail view
10. **[15A-010]** Implement push notifications
11. **[15A-011]** Build SettingsScreen + app preferences
12. **[15A-012]** Unit test suite (>85% coverage)
13. **[15A-013]** E2E tests (critical user flows)

### Tier 3: App Store (Week 5)
14. **[15A-014]** iOS app signing & App Store submission
15. **[15A-015]** Android app signing & Google Play submission
16. **[15A-016]** App store review & approval monitoring

---

## Initial Ticket List - TRACK B (Advanced Predictions)

### Tier 1: Foundation (Week 1-2)
1. **[15B-001]** Data preparation & EDA
   - Assignee: Data Scientist
   - Effort: 1.5d
   - Depends: None
   - Includes: Load data, quality assessment, outlier detection

2. **[15B-002]** Feature engineering & preprocessing
   - Assignee: ML Engineer
   - Effort: 2d
   - Depends: 15B-001
   - Includes: Feature matrix creation, scaling, encoding

3. **[15B-003]** ML model selection & training
   - Assignee: ML Engineer
   - Effort: 1.5d
   - Depends: 15B-002
   - Model: RandomForestClassifier

4. **[15B-004]** Model evaluation & cross-validation
   - Assignee: Data Scientist
   - Effort: 1d
   - Depends: 15B-003
   - Target: >70% accuracy

5. **[15B-005]** SHAP integration for explainability
   - Assignee: ML Engineer
   - Effort: 1.5d
   - Depends: 15B-003
   - Includes: Feature importance, SHAP values

6. **[15B-006]** Predictions API endpoints
   - Assignee: Full-Stack Dev
   - Effort: 1.5d
   - Depends: 15B-003
   - Endpoints: /api/predictions/generate, /api/predictions/{id}/explanation

7. **[15B-007]** Database schema updates & indexes
   - Assignee: Data Engineer
   - Effort: 1d
   - Depends: None
   - Tables: prediction_history, model_metadata

8. **[15B-008]** Batch prediction job (scheduled)
   - Assignee: Full-Stack Dev
   - Effort: 1.5d
   - Depends: 15B-006, 15B-007

9. **[15B-009]** A/B test framework (ML vs rule-based)
   - Assignee: Data Scientist
   - Effort: 1.5d
   - Depends: 15B-006
   - Includes: Random assignment, tracking, statistical test

### Tier 2: Integration (Week 3-4)
10. **[15B-010]** Dashboard widget for explainability
11. **[15B-011]** Accuracy tracking & historical comparison
12. **[15B-012]** Model retraining pipeline
13. **[15B-013]** Unit test suite (>85% coverage)

### Tier 3: Refinement (Week 5)
14. **[15B-014]** Hyperparameter tuning & optimization
15. **[15B-015]** Production model deployment & serving
16. **[15B-016]** Monitoring & alerting for model performance

---

## Critical Path & Dependencies

```
TRACK A:
  ┌─→ [15A-001] Setup (1d)
  │   ├─→ [15A-002] Auth (2d)
  │   ├─→ [15A-003] Redux (1d)
  │   │   └─→ [15A-004] Navigation (1d)
  │   ├─→ [15A-005] WebSocket (1.5d)
  │   └─→ [15A-007] Offline (1.5d)
  └─→ [15A-006] Dashboard (2d) [depends 15A-003, 15A-005]
      └─→ [15A-008] Performance (1d)

CRITICAL PATH: 1 + 2 + 1 + 2 = 6 days minimum

TRACK B:
  ┌─→ [15B-001] EDA (1.5d)
  │   └─→ [15B-002] Features (2d)
  │       └─→ [15B-003] Model Train (1.5d)
  │           ├─→ [15B-004] Eval (1d)
  │           └─→ [15B-005] SHAP (1.5d)
  │               └─→ [15B-006] API (1.5d)
  │
  ├─→ [15B-007] DB Schema (1d) [parallel]
  │   └─→ [15B-008] Batch Job (1.5d)
  │
  └─→ [15B-009] A/B Test (1.5d) [depends 15B-006]

CRITICAL PATH: 1.5 + 2 + 1.5 + 1 + 1.5 + 1.5 = 9 days minimum
```

**Both tracks can run in parallel, starting Monday Oct 7.**

---

## Success Criteria - Sprint 1

### Functionality ✅
- [ ] Mobile app runs on iOS + Android simulators
- [ ] Login/auth flow working with mock data
- [ ] DashboardScreen displaying real-time predictions (mock WebSocket)
- [ ] Offline caching working (AsyncStorage + sync queue)
- [ ] ML model trained with >70% accuracy
- [ ] Predictions API returning results
- [ ] SHAP explainability working
- [ ] A/B test framework ready

### Code Quality ✅
- [ ] All new code has >85% test coverage
- [ ] Linting passes (ESLint, pylint)
- [ ] No security issues (bandit scan)
- [ ] Code review completed by track leads

### Performance ✅
- [ ] Mobile app loads <1.5s on 4G network
- [ ] WebSocket latency <100ms
- [ ] Prediction API response time <500ms
- [ ] Batch prediction job completes for 1,000 clients in <5 min

### Git & CI/CD ✅
- [ ] Feature branches pushed with clean commit history
- [ ] GitHub Actions CI/CD passing
- [ ] Staging deployment successful
- [ ] Team can pull, build, and run both tracks locally

---

## Team Roles & Responsibilities

### TRACK A: Mobile Apps (4 people)

**Lead Mobile Developer** (Senior)
- Architecture decisions
- Code review for mobile PRs
- WebSocket + offline implementation
- Performance optimization

**Mobile Developer 2**
- Auth system implementation
- UI/UX screens
- Redux state management
- Testing

**iOS QA Tester**
- iOS simulator testing
- Biometric auth testing
- App Store submission support

**Android QA Tester**
- Android emulator testing
- Material Design compliance
- Google Play submission support

### TRACK B: Advanced Predictions (4 people)

**ML Engineer** (Senior)
- Model selection & training
- Feature engineering
- SHAP integration
- Hyperparameter tuning

**Data Scientist**
- EDA & data quality assessment
- Model evaluation
- A/B test statistical analysis
- Accuracy validation

**Full-Stack Developer**
- Predictions API endpoints
- Batch job scheduling
- Database integration
- Dashboard widgets

**Data Engineer**
- Database schema design
- Data pipeline optimization
- Retraining automation
- Monitoring setup

---

## Next Steps (Upon Sprint 1 Completion)

**Friday Oct 18 (End of Sprint 1):**
- [ ] Daily standup: sprint review with both tracks
- [ ] Demo: mobile prototype + predictions API
- [ ] Retrospective: what worked, what to improve
- [ ] Sprint 1 release notes drafted

**Monday Oct 21 (Sprint 2 Kickoff):**
- [ ] Push merged code to staging environment
- [ ] Integration testing: mobile ↔ backend
- [ ] Begin Sprint 2: Polish & Refinement
  - Track A: PredictionsScreen, push notifications, more screens
  - Track B: Model optimization, accuracy tracking, retraining pipeline

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Expo build complications | Medium | Medium | Have bare RN as fallback; investigate early |
| WebSocket connection instability | Medium | High | Extensive reconnection testing; implement exponential backoff |
| ML model accuracy <70% | Medium | High | Have rule-based fallback; A/B test for winner determination |
| Mobile performance degradation | Low | High | Profile from day 1; lazy load charts; virtualize lists |
| Team coordination issues | Low | Medium | Daily standups; slack channel #fase-15; weekly sync |

---

**Document Version:** 1.0  
**Created:** 2026-10-06 19:30 CLT  
**Status:** 🎯 READY FOR SPRINT 1 KICKOFF (Oct 7, 2026)  
**Next Review:** Oct 11, 2026 (End of Week 1)
