# FASE 15 - Initial Tickets & Backlog

**Created:** 2026-10-06  
**Sprint:** Sprint 1 (Oct 7-20, 2026)  
**Total Tickets:** 32 (16 per track)  
**Effort:** ~48 days (parallelized across 8 developers = ~6 days per developer)  

---

## 📋 Ticket Format

Each ticket includes:
- **ID:** `[15A-XXX]` (Track A) or `[15B-XXX]` (Track B)
- **Title:** Clear, action-oriented name
- **Description:** What needs to be done
- **Acceptance Criteria:** When this ticket is "done"
- **Effort:** Days of work (1d = 8 hours)
- **Assignee:** Developer name (to be filled)
- **Dependencies:** Blocking tickets (if any)
- **Labels:** sprint, priority, component

---

## TRACK A: Mobile Apps (iOS + Android)

### Sprint 1: Foundation & Architecture (Oct 7-20)

#### [15A-001] Setup React Native Project Scaffold

**Priority:** 🔴 CRITICAL  
**Effort:** 1 day  
**Assignee:** Lead Mobile Dev  
**Dependencies:** None  
**Status:** Ready to start

**Description:**
Initialize a React Native project using Expo that will serve as the foundation for iOS and Android apps.

**Acceptance Criteria:**
- [ ] React Native project initialized with Expo 51.0+
- [ ] Project structure created with src/, components/, screens/ folders
- [ ] TypeScript configured with tsconfig.json
- [ ] ESLint + Prettier setup for code quality
- [ ] .gitignore excludes node_modules, .expo, build artifacts
- [ ] App runs on both iOS Simulator and Android Emulator
- [ ] Dev team can clone repo, run `npm install`, then `npm start`
- [ ] Initial "Hello World" screen renders successfully
- [ ] Git branch `feat/mobile-core-setup` created and pushed

**Technical Notes:**
- Use Expo (not bare React Native) for faster iteration
- Include: @react-native/core, react-native-reanimated (for smooth animations)
- Package.json should have scripts: start, test, lint, format
- Configure app.json with app name, icons, splash screen

**Definition of Done:**
- Code review passed
- All setup scripts verified
- Documentation updated in README.md

---

#### [15A-002] Implement Authentication System (Biometric + Password)

**Priority:** 🔴 CRITICAL  
**Effort:** 2 days  
**Assignee:** Mobile Dev 2  
**Dependencies:** [15A-001]  
**Status:** Waiting for 15A-001

**Description:**
Build complete authentication flow with biometric support (iOS Keychain, Android BiometricPrompt) and password fallback.

**Acceptance Criteria:**
- [ ] LoginScreen component created with email/password inputs
- [ ] Biometric authentication using `react-native-biometrics` library
- [ ] Keychain storage via `react-native-keychain` (secure token storage)
- [ ] Biometric fallback to password on unsupported devices
- [ ] JWT token refresh logic implemented
- [ ] Session timeout after 24 hours
- [ ] Unit tests for auth logic (>85% coverage)
- [ ] Mock auth service for development
- [ ] Error handling for failed login attempts
- [ ] Loading states and error messages displayed

**Technical Notes:**
- Libraries: react-native-biometrics, react-native-keychain
- Integrate with Redux auth slice (from 15A-003)
- API calls to `/api/auth/login` and `/api/auth/refresh`
- Store JWT in secure keychain, not local storage

**Acceptance Criteria - Testing:**
- [ ] Login with email/password works in simulator
- [ ] Biometric prompt appears on supported devices
- [ ] Fallback to password works on unsupported devices
- [ ] Invalid credentials show error message
- [ ] Tokens refreshed silently before expiration

**Definition of Done:**
- [ ] Code review passed
- [ ] Test coverage >85%
- [ ] PR merged to develop
- [ ] Documentation added to README

---

#### [15A-003] Setup Redux State Management

**Priority:** 🔴 CRITICAL  
**Effort:** 1 day  
**Assignee:** Lead Mobile Dev  
**Dependencies:** [15A-001]  
**Status:** Waiting for 15A-001

**Description:**
Implement Redux Toolkit for centralized state management across the mobile app.

**Acceptance Criteria:**
- [ ] Redux store created with Redux Toolkit
- [ ] Slices created: auth, dashboard, predictions, ui
- [ ] Redux DevTools integration for debugging
- [ ] Middleware: logger, error handler
- [ ] Redux hooks: useAppDispatch, useAppSelector (typed)
- [ ] Async thunks for API calls
- [ ] Error handling middleware
- [ ] Selectors for common queries (isLoggedIn, currentClient, etc.)
- [ ] Unit tests for reducers (>85% coverage)

**Slices Structure:**
```javascript
// authSlice
- state.token
- state.user
- state.isLoading
- actions: login, logout, refreshToken, setUser
- thunks: loginAsync, refreshTokenAsync

// dashboardSlice
- state.clients (list)
- state.selectedClient (current)
- state.predictions (real-time)
- state.filters
- actions: setSelectedClient, updatePredictions

// predictionsSlice
- state.predictions (list)
- state.details (single prediction detail)
- state.isLoading
- actions: setPredictions, setPredictionDetail

// uiSlice
- state.showMenu
- state.showNotification
- state.theme (light/dark)
- actions: toggleMenu, showNotification
```

**Technical Notes:**
- Use Redux Toolkit (createSlice, createAsyncThunk)
- Configure store with middleware
- Add redux-persist for offline state (optional for Phase 2)

**Definition of Done:**
- [ ] Redux store working with all slices
- [ ] DevTools accessible in development
- [ ] Tests passing for all reducers
- [ ] Documentation in code comments

---

#### [15A-004] Implement React Navigation

**Priority:** 🔴 CRITICAL  
**Effort:** 1 day  
**Assignee:** Mobile Dev 2  
**Dependencies:** [15A-001], [15A-003]  
**Status:** Waiting for 15A-003

**Description:**
Set up React Navigation with Stack and Tab navigators for app flow (login → dashboard → predictions).

**Acceptance Criteria:**
- [ ] Navigation containers setup (NavigationContainer)
- [ ] Stack Navigator for authentication flow
- [ ] Bottom Tab Navigator for main app (dashboard, predictions, settings)
- [ ] Authentication check: redirect to login if not authenticated
- [ ] Smooth transitions between screens
- [ ] Deep linking support (optional for Phase 2)
- [ ] Navigation state persisted across app restarts (optional)
- [ ] Unit tests for navigation (>85% coverage)

**Navigation Structure:**
```
RootNavigator
├── Auth Stack (when not logged in)
│   └── LoginScreen
└── App Stack (when logged in)
    ├── Dashboard Tab
    │   ├── DashboardScreen
    │   └── ClientDetail Stack
    ├── Predictions Tab
    │   └── PredictionsScreen
    └── Settings Tab
        └── SettingsScreen
```

**Technical Notes:**
- Libraries: @react-navigation/native, @react-navigation/bottom-tabs, @react-navigation/stack
- Connect to Redux auth state for conditional rendering
- Use useIsFocused hook for screen-specific logic

**Definition of Done:**
- [ ] Navigation working end-to-end
- [ ] All screens reachable from navigation
- [ ] Back button behavior correct
- [ ] Tests passing

---

#### [15A-005] Create WebSocket Client Service

**Priority:** 🔴 CRITICAL  
**Effort:** 1.5 days  
**Assignee:** Lead Mobile Dev  
**Dependencies:** [15A-001], [15A-003]  
**Status:** Waiting for 15A-003

**Description:**
Build WebSocket service for real-time updates from backend, with automatic reconnection and heartbeat.

**Acceptance Criteria:**
- [ ] WebSocketService singleton created
- [ ] Connection establishment with JWT authentication
- [ ] Auto-reconnection with exponential backoff (1s, 2s, 4s, 8s...)
- [ ] Heartbeat/ping-pong for mobile networks (reduce battery drain)
- [ ] Event listener pattern for different message types
- [ ] Redux integration: dispatch actions on events
- [ ] Connection status indicator (connected, disconnected, reconnecting)
- [ ] Error handling and logging
- [ ] Unit tests for connection lifecycle (>85% coverage)

**WebSocket Events to Handle:**
```
- prediction:generated → Update dashboard
- test:started → Show notification
- test:completed → Update results
- anomaly:detected → Alert user
- update:available → Prompt app update
```

**Technical Notes:**
- Use native WebSocket API (built into React Native)
- Implement exponential backoff for reconnection
- Mobile heartbeat: 60s interval (vs 30s on desktop)
- Store connection state in Redux ui slice

**Definition of Done:**
- [ ] WebSocket connects on app startup
- [ ] Events dispatched to Redux correctly
- [ ] Reconnection working in airplane mode test
- [ ] Heartbeat reducing battery drain
- [ ] Tests passing

---

#### [15A-006] Build DashboardScreen (Real-Time Predictions)

**Priority:** 🔴 CRITICAL  
**Effort:** 2 days  
**Assignee:** Mobile Dev 2  
**Dependencies:** [15A-003], [15A-005]  
**Status:** Waiting for 15A-005

**Description:**
Create main dashboard screen showing real-time sales predictions and client information.

**Acceptance Criteria:**
- [ ] DashboardScreen component created
- [ ] Display list of clients with latest predictions
- [ ] Real-time probability gauge (0-100% circular dial)
- [ ] Confidence indicator (colored bar with %)
- [ ] Risk factors list (collapsible, highlighted)
- [ ] Positive factors list (expandable, highlighted)
- [ ] Recommended timeline to close (days estimate)
- [ ] Pull-to-refresh to manually update
- [ ] Mock data displayed until backend ready
- [ ] Performance: <1.5s initial load on 4G
- [ ] Unit + integration tests (>85% coverage)

**UI Components:**
```
┌─────────────────────────────────┐
│  DASHBOARD                 👤  │
├─────────────────────────────────┤
│  Client: Acme Corp             │
│  ┌───────────────┐             │
│  │      72%      │ Conversion  │
│  │  Confidence   │ Probability │
│  │      88       │             │
│  └───────────────┘             │
│                                 │
│  ⚠️  Risk Factors:              │
│  • Budget concerns              │
│  • Delayed decision              │
│  • 3 stakeholders               │
│                                 │
│  ✅ Positive Factors:           │
│  • Active engagement            │
│  • Quick response time          │
│  • Team availability            │
│                                 │
│  ⏱️  Timeline: ~14 days         │
│                                 │
│  [← Clients] [Details →]       │
└─────────────────────────────────┘
```

**Technical Notes:**
- Use react-native-svg for gauge visualization
- Redux selectors: selectedClient, clientPredictions
- Real-time updates from WebSocket
- Pull-to-refresh: RefreshControl component

**Definition of Done:**
- [ ] Dashboard rendering correctly
- [ ] Real-time updates visible
- [ ] Performance benchmarks met
- [ ] Accessibility features (touch targets 44x44px)
- [ ] Tests passing

---

#### [15A-007] Implement Offline Capability (AsyncStorage + Sync Queue)

**Priority:** 🟡 HIGH  
**Effort:** 1.5 days  
**Assignee:** Lead Mobile Dev  
**Dependencies:** [15A-003], [15A-006]  
**Status:** Waiting for 15A-006

**Description:**
Add offline support by caching data locally and syncing when connection restored.

**Acceptance Criteria:**
- [ ] AsyncStorage setup for data persistence
- [ ] Cache strategy: cache essential data (clients, predictions)
- [ ] Sync queue: store actions taken offline (e.g., mark as contacted)
- [ ] On reconnect: sync queued actions back to server
- [ ] Conflict resolution if offline edits conflict with server
- [ ] Clear indication when app is offline
- [ ] Manual sync button for user control
- [ ] Automatic cleanup of old cache (>7 days)
- [ ] Unit tests for offline flow (>85% coverage)

**Offline Data to Cache:**
- Client list + details
- Recent predictions
- Conversation history

**Queued Actions:**
- Mark client as "contacted"
- Add note to client
- Update client status

**Technical Notes:**
- Use AsyncStorage or expo-sqlite for local DB
- Redux middleware for sync queue logic
- Conflict resolution: last-write-wins or prompt user
- Test with network disabled (Device Settings)

**Definition of Done:**
- [ ] App fully functional offline
- [ ] Sync working on reconnect
- [ ] No data loss
- [ ] Tests passing

---

#### [15A-008] Performance Optimization & Profiling

**Priority:** 🟡 HIGH  
**Effort:** 1 day  
**Assignee:** Mobile Dev 2  
**Dependencies:** [15A-006]  
**Status:** Waiting for 15A-006

**Description:**
Optimize mobile app performance to meet <1.5s load time target on 4G networks.

**Acceptance Criteria:**
- [ ] Dashboard load time <1.5s on 4G (tested with throttling)
- [ ] Lazy load charts (render only when visible)
- [ ] Virtualize long lists (PredictionsScreen, ClientList)
- [ ] Memoize expensive computations (useMemo)
- [ ] Debounce search/filter inputs
- [ ] Image optimization (compress, use appropriate formats)
- [ ] Remove console.log statements
- [ ] React Profiler used to identify bottlenecks
- [ ] FPS stays >50 during scrolling (60fps on new devices)
- [ ] Memory usage <200MB during normal use
- [ ] Benchmark report created

**Profiling Tools:**
- React Native Debugger
- React Profiler (built-in DevTools)
- Flipper (Facebook debugging tool)

**Optimization Techniques:**
- Code splitting (for future native builds)
- Tree shaking (remove unused code)
- Asset compression
- List virtualization (FlatList with windowSize optimization)

**Definition of Done:**
- [ ] Load time <1.5s verified
- [ ] Benchmarks documented
- [ ] No regression in functionality
- [ ] Memory usage acceptable

---

### Sprint 2: Additional Screens & Features (Oct 21-Nov 3)

#### [15A-009] Build PredictionsScreen with Detail View

**Priority:** 🟡 HIGH  
**Effort:** 1.5 days  
**Assignee:** Mobile Dev 2  
**Dependencies:** [15A-006]  
**Status:** Waiting for Sprint 2

**Description:**
Create detailed predictions screen showing individual prediction details and historical accuracy.

**Acceptance Criteria:**
- [ ] List all predictions for selected client
- [ ] Tap to view prediction details
- [ ] Show SHAP explainability (why 72%?)
- [ ] Historical predictions comparison
- [ ] Mark prediction as "used" or "archived"
- [ ] Share prediction (email, messaging)
- [ ] Pagination or infinite scroll for large lists
- [ ] Tests (>85% coverage)

---

#### [15A-010] Implement Push Notifications

**Priority:** 🟡 HIGH  
**Effort:** 1.5 days  
**Assignee:** Lead Mobile Dev  
**Dependencies:** [15A-001]  
**Status:** Waiting for Sprint 2

**Description:**
Add push notification support for new predictions and important events.

**Acceptance Criteria:**
- [ ] Firebase Cloud Messaging (FCM) integration
- [ ] Permission request on first app launch
- [ ] Foreground + background notification handling
- [ ] Notification deep links (open specific prediction)
- [ ] Local notification for testing
- [ ] Notification preferences screen
- [ ] Badge count on app icon
- [ ] Tests (>85% coverage)

---

#### [15A-011] Build SettingsScreen

**Priority:** 🟢 LOW  
**Effort:** 1 day  
**Assignee:** Mobile Dev 2  
**Dependencies:** [15A-004]  
**Status:** Waiting for Sprint 2

**Description:**
Settings screen for user preferences and app configuration.

**Acceptance Criteria:**
- [ ] Theme toggle (light/dark mode)
- [ ] Notification preferences
- [ ] Language selection (EN/ES)
- [ ] About app section
- [ ] Logout button
- [ ] App version display
- [ ] Tests (>85% coverage)

---

#### [15A-012] Unit Test Suite (>85% Coverage)

**Priority:** 🟡 HIGH  
**Effort:** 1.5 days  
**Assignee:** Mobile Dev 2  
**Dependencies:** All components  
**Status:** Waiting for Sprint 2

**Description:**
Comprehensive unit test coverage for all components and hooks.

**Acceptance Criteria:**
- [ ] Test coverage >85% for entire mobile app
- [ ] All reducers tested
- [ ] All components tested with React Native Testing Library
- [ ] All hooks tested
- [ ] CI/CD pipeline passing all tests
- [ ] Coverage report generated

---

#### [15A-013] E2E Tests (Critical User Flows)

**Priority:** 🟡 HIGH  
**Effort:** 1 day  
**Assignee:** Lead Mobile Dev  
**Dependencies:** [15A-012]  
**Status:** Waiting for Sprint 2

**Description:**
End-to-end tests for critical user workflows.

**Acceptance Criteria:**
- [ ] Test: Login → View Dashboard → View Predictions → Logout
- [ ] Test: Offline mode → Make changes → Reconnect → Sync
- [ ] Test: Push notification received → Tap → Open prediction
- [ ] All tests passing on iOS + Android
- [ ] Tests documented in runbook

---

### Sprint 3: App Store Submission (Nov 4-10)

#### [15A-014] iOS App Signing & App Store Submission

**Priority:** 🔴 CRITICAL  
**Effort:** 1 day  
**Assignee:** Lead Mobile Dev  
**Dependencies:** [15A-013]  
**Status:** Waiting for Sprint 3

**Description:**
Build and submit iOS app to Apple App Store for review.

**Acceptance Criteria:**
- [ ] App signing certificate created (Apple Developer account)
- [ ] App provisioning profile configured
- [ ] App icons designed (1024x1024 minimum)
- [ ] Launch screen configured
- [ ] Privacy policy added to app
- [ ] App Store listing created
- [ ] Screenshots prepared (5-6 per screen)
- [ ] Release notes drafted
- [ ] EAS Build executed for iOS
- [ ] Submission to App Store complete
- [ ] App status tracked in App Store Connect

---

#### [15A-015] Android App Signing & Google Play Submission

**Priority:** 🔴 CRITICAL  
**Effort:** 1 day  
**Assignee:** Mobile Dev 2  
**Dependencies:** [15A-013]  
**Status:** Waiting for Sprint 3

**Description:**
Build and submit Android app to Google Play Store for review.

**Acceptance Criteria:**
- [ ] Keystore created for signing
- [ ] App icons designed (512x512 minimum + adaptive icon)
- [ ] App Store listing created
- [ ] Privacy policy added
- [ ] Screenshots prepared (4-5 per screen)
- [ ] Release notes drafted
- [ ] EAS Build executed for Android
- [ ] Submission to Google Play Store complete
- [ ] App status tracked in Google Play Console

---

#### [15A-016] App Store Review & Approval Monitoring

**Priority:** 🟡 HIGH  
**Effort:** 1 day  
**Assignee:** Lead Mobile Dev  
**Dependencies:** [15A-014], [15A-015]  
**Status:** Waiting for Sprint 3

**Description:**
Monitor app review progress and handle any rejections/feedback.

**Acceptance Criteria:**
- [ ] Monitor App Store review status daily
- [ ] Monitor Google Play review status daily
- [ ] Respond to any reviewer feedback
- [ ] Resubmit if rejected
- [ ] Track approval timeline
- [ ] Prepare marketing announcement when approved
- [ ] Version 1.0.0 deployed to production

---

## TRACK B: Advanced Predictions (ML Engine)

### Sprint 1: Foundation & Architecture (Oct 7-20)

#### [15B-001] Data Preparation & Exploratory Data Analysis (EDA)

**Priority:** 🔴 CRITICAL  
**Effort:** 1.5 days  
**Assignee:** Data Scientist  
**Dependencies:** None  
**Status:** Ready to start

**Description:**
Load FASE 14 historical data and perform comprehensive exploratory analysis to understand patterns and quality.

**Acceptance Criteria:**
- [ ] Load 5,432 historical predictions from FASE 14
- [ ] Load actual outcomes from CRM (if available)
- [ ] Data quality assessment: missing values, outliers, duplicates
- [ ] Statistical summary: mean, median, std dev, distribution
- [ ] Identify class imbalance (conversion vs no conversion)
- [ ] Correlation analysis between features and target
- [ ] Visualizations: histograms, scatter plots, heatmaps
- [ ] Feature distribution analysis
- [ ] Identify potential data quality issues
- [ ] EDA notebook created (Jupyter)
- [ ] Summary report with recommendations

**Deliverables:**
- Jupyter notebook: `notebooks/01_eda.ipynb`
- Data quality report
- Feature correlation heatmap
- Class distribution visualization

**Technical Notes:**
- Tools: pandas, numpy, matplotlib, seaborn
- Target variable: conversion_yes/no (binary classification)
- Features: client_size, industry, budget, engagement_score, etc.

**Definition of Done:**
- [ ] EDA complete and documented
- [ ] Data quality issues identified
- [ ] Ready for feature engineering

---

#### [15B-002] Feature Engineering & Preprocessing

**Priority:** 🔴 CRITICAL  
**Effort:** 2 days  
**Assignee:** ML Engineer  
**Dependencies:** [15B-001]  
**Status:** Waiting for 15B-001

**Description:**
Transform raw features into ML-ready features with proper scaling and encoding.

**Acceptance Criteria:**
- [ ] Create feature matrix (clients × features)
- [ ] Handle categorical variables: one-hot encoding for industry
- [ ] Numeric scaling: StandardScaler for numeric features
- [ ] Handle missing values: imputation strategy documented
- [ ] Handle outliers: detection and removal/treatment strategy
- [ ] Feature selection: identify top 15-20 most important features
- [ ] Create preprocessing pipeline (scikit-learn Pipeline)
- [ ] Test/verify feature engineering on sample data
- [ ] Documentation: which features used and why
- [ ] Unit tests for preprocessing (>85% coverage)

**Feature Engineering Examples:**
- Client company size (feature)
- Industry category (feature, one-hot encoded)
- Days since first contact (feature)
- Number of emails sent (feature)
- Engagement score (feature, derived)
- Budget tier (feature, categorical)

**Technical Notes:**
- Use sklearn.preprocessing: StandardScaler, OneHotEncoder
- Create ColumnTransformer for mixed feature types
- Save preprocessing objects for inference later
- Document feature rationale in code comments

**Deliverables:**
- Jupyter notebook: `notebooks/02_feature_engineering.ipynb`
- Feature preprocessing pipeline code
- Feature list documentation

**Definition of Done:**
- [ ] Feature matrix ready for modeling
- [ ] Preprocessing pipeline tested
- [ ] Documentation complete

---

#### [15B-003] ML Model Selection & Training

**Priority:** 🔴 CRITICAL  
**Effort:** 1.5 days  
**Assignee:** ML Engineer  
**Dependencies:** [15B-002]  
**Status:** Waiting for 15B-002

**Description:**
Train RandomForest model on historical data with cross-validation.

**Acceptance Criteria:**
- [ ] Choose RandomForestClassifier (scikit-learn)
- [ ] 80-20 train-test split (4,346 train / 1,086 test)
- [ ] 5-fold cross-validation for robustness
- [ ] Hyperparameter tuning with GridSearchCV
- [ ] Model trained on full training set with best params
- [ ] Model saved to disk (pickle format)
- [ ] Preprocessing transformer saved alongside model
- [ ] Training time documented (<5 minutes for full dataset)
- [ ] Model loading utility created for inference
- [ ] Unit tests for model loading (>85% coverage)

**Hyperparameters to Tune:**
- n_estimators: 100, 200, 300
- max_depth: 10, 15, 20, None
- min_samples_split: 2, 5, 10
- min_samples_leaf: 1, 2, 4

**Deliverables:**
- Trained model: `models/conversion_predictor_v1.pkl`
- Preprocessing transformer: `models/preprocessor_v1.pkl`
- Model loading code in `backend/analytics/ml_pipeline.py`
- Jupyter notebook: `notebooks/03_model_training.ipynb`

**Technical Notes:**
- Use sklearn.ensemble.RandomForestClassifier
- Configure random_state=42 for reproducibility
- Use sklearn.model_selection.GridSearchCV for tuning
- Log training metrics (time, cross-val scores)

**Definition of Done:**
- [ ] Model trained and saved
- [ ] Cross-validation scores >70%
- [ ] Model loading tested
- [ ] Documentation complete

---

#### [15B-004] Model Evaluation & Cross-Validation

**Priority:** 🔴 CRITICAL  
**Effort:** 1 day  
**Assignee:** Data Scientist  
**Dependencies:** [15B-003]  
**Status:** Waiting for 15B-003

**Description:**
Thoroughly evaluate model performance and validate accuracy metrics.

**Acceptance Criteria:**
- [ ] Accuracy on test set: target >70%
- [ ] Confusion matrix analysis: TP, TN, FP, FN
- [ ] Precision, Recall, F1-score calculated
- [ ] ROC-AUC score calculated (target >0.75)
- [ ] Learning curves plotted (train vs validation)
- [ ] Cross-validation scores reported (mean ± std)
- [ ] Feature importance extracted (top 10 features)
- [ ] Comparison with baseline (rule-based system)
- [ ] Error analysis: what does model get wrong?
- [ ] Documentation of metrics and interpretation

**Metrics to Report:**
```
Accuracy: X.XX%
Precision: X.XX%
Recall: X.XX%
F1-Score: X.XX
ROC-AUC: X.XX

Confusion Matrix:
        Predicted No  Predicted Yes
Actual No    XXX          XX
Actual Yes   XXX          XXX
```

**Deliverables:**
- Evaluation report with all metrics
- Confusion matrix visualization
- Feature importance plot
- Learning curves plot
- Baseline comparison

**Definition of Done:**
- [ ] All metrics calculated
- [ ] Accuracy >70% confirmed
- [ ] Results documented
- [ ] Ready for production

---

#### [15B-005] SHAP Integration for Explainability

**Priority:** 🔴 CRITICAL  
**Effort:** 1.5 days  
**Assignee:** ML Engineer  
**Dependencies:** [15B-003]  
**Status:** Waiting for 15B-003

**Description:**
Integrate SHAP (SHapley Additive exPlanations) for model interpretability.

**Acceptance Criteria:**
- [ ] SHAP values calculated for all predictions
- [ ] Feature importance summary plot created
- [ ] Force plots for individual predictions (why 72%?)
- [ ] Bar plots showing positive/negative factors
- [ ] SHAP explainability module created (`backend/analytics/explainability.py`)
- [ ] Explain function: takes prediction, returns top factors
- [ ] Unit tests for SHAP calculations (>85% coverage)
- [ ] Documentation of interpretation

**SHAP Deliverables:**
```python
def explain_prediction(model, preprocessor, client_features):
    """
    Returns:
    {
        'probability': 0.72,
        'confidence': 0.88,
        'top_positive_factors': [
            {'name': 'engagement_score', 'contribution': +0.25},
            {'name': 'budget_tier', 'contribution': +0.18},
        ],
        'top_negative_factors': [
            {'name': 'days_since_contact', 'contribution': -0.12},
            {'name': 'competitor_mentioned', 'contribution': -0.08},
        ]
    }
    ```

**Visualizations:**
- Summary plot (global feature importance)
- Force plot (individual prediction)
- Dependence plot (feature interaction)

**Technical Notes:**
- Libraries: shap, matplotlib
- SHAP base value = model's average output
- SHAP value = contribution to difference from base value
- TreeExplainer for RandomForest

**Deliverables:**
- Explainability module code
- SHAP integration tests
- Example explanations for sample predictions
- Jupyter notebook: `notebooks/04_shap_explainability.ipynb`

**Definition of Done:**
- [ ] SHAP values calculated correctly
- [ ] Explanations understandable to business users
- [ ] API ready for dashboard integration

---

#### [15B-006] Predictions API Endpoints

**Priority:** 🔴 CRITICAL  
**Effort:** 1.5 days  
**Assignee:** Full-Stack Dev  
**Dependencies:** [15B-003], [15B-005]  
**Status:** Waiting for 15B-005

**Description:**
Build FastAPI endpoints for prediction generation and explainability.

**Acceptance Criteria:**
- [ ] `POST /api/predictions/generate` endpoint
  - Input: client_id + client attributes
  - Output: probability, confidence, risk_factors, positive_factors
  - Load model from disk, run inference, return results
- [ ] `GET /api/predictions/{id}/explanation` endpoint
  - Returns SHAP explanation for prediction
  - Shows top 5 positive and negative factors
- [ ] Error handling for invalid inputs
- [ ] Rate limiting: 100 req/sec
- [ ] Request validation with Pydantic
- [ ] Response caching (optional, for performance)
- [ ] Unit tests (>85% coverage)
- [ ] Integration tests with mock client data

**API Examples:**

```bash
# Generate prediction
curl -X POST http://localhost:8000/api/predictions/generate \
  -H "Content-Type: application/json" \
  -d '{"client_id": 123, "company_size": "medium", "budget": 50000}'

# Response:
{
  "client_id": 123,
  "probability": 0.72,
  "confidence": 0.88,
  "risk_factors": [...],
  "positive_factors": [...],
  "recommendation": "Follow up within 14 days"
}

# Get explanation
curl http://localhost:8000/api/predictions/123/explanation

# Response:
{
  "prediction_id": 123,
  "positive_factors": [
    {"name": "engagement_score", "contribution": 0.25},
    ...
  ],
  "negative_factors": [...]
}
```

**Technical Notes:**
- Load model once on app startup (not on every request)
- Use FastAPI dependency injection for model access
- Implement request/response logging

**Deliverables:**
- API endpoints in `backend/routes/predictions_routes.py`
- Pydantic models for request/response
- Integration tests

**Definition of Done:**
- [ ] Endpoints working end-to-end
- [ ] Tests passing
- [ ] Documentation generated (Swagger)

---

#### [15B-007] Database Schema Updates & Indexes

**Priority:** 🔴 CRITICAL  
**Effort:** 1 day  
**Assignee:** Data Engineer  
**Dependencies:** None  
**Status:** Ready to start (parallel with other tasks)

**Description:**
Update database schema to store predictions and model metadata.

**Acceptance Criteria:**
- [ ] `prediction_history` table created
  - Columns: id, client_id, probability, confidence, created_at, actual_outcome
  - Indexes: client_id, created_at
- [ ] `model_metadata` table created
  - Columns: id, version, accuracy, trained_at, model_path
  - Stores info about trained models
- [ ] Migrations created (if using Alembic)
- [ ] Indexes on frequently queried columns
- [ ] Query performance verified (<50ms for common queries)
- [ ] Database migration tested on fresh DB
- [ ] Backup procedure documented

**Schema:**
```sql
CREATE TABLE prediction_history (
  id INTEGER PRIMARY KEY,
  client_id INTEGER NOT NULL,
  probability REAL,
  confidence REAL,
  risk_factors JSON,
  positive_factors JSON,
  created_at TIMESTAMP,
  actual_outcome BOOLEAN,  -- NULL until known
  FOREIGN KEY (client_id) REFERENCES clients(id),
  INDEX idx_client_created (client_id, created_at)
);

CREATE TABLE model_metadata (
  id INTEGER PRIMARY KEY,
  version TEXT,
  accuracy REAL,
  trained_at TIMESTAMP,
  model_path TEXT
);
```

**Definition of Done:**
- [ ] Schema created and tested
- [ ] Indexes verified
- [ ] Migration documented

---

#### [15B-008] Batch Prediction Job (Scheduled)

**Priority:** 🟡 HIGH  
**Effort:** 1.5 days  
**Assignee:** Full-Stack Dev  
**Dependencies:** [15B-006], [15B-007]  
**Status:** Waiting for 15B-007

**Description:**
Scheduled job to generate predictions for all clients daily/weekly.

**Acceptance Criteria:**
- [ ] APScheduler job configured
- [ ] Run daily at 2am CLT (off-peak)
- [ ] Process all clients in batches (100 at a time)
- [ ] Generate prediction for each client
- [ ] Store in prediction_history table
- [ ] Calculate accuracy vs actual outcomes (if available)
- [ ] Log job execution and metrics
- [ ] Error handling and retry logic
- [ ] Monitoring: alert if job fails
- [ ] Unit tests (>85% coverage)

**Job Logic:**
```python
@scheduled_job('cron', hour=2, minute=0, timezone='America/Santiago')
def daily_batch_predictions():
    clients = get_all_clients(batch_size=100)
    for batch in clients:
        for client in batch:
            prediction = generate_prediction(client)
            save_prediction_history(prediction)
    log_job_completion()
```

**Deliverables:**
- Batch job code in `backend/analytics/batch_predictor.py`
- APScheduler configuration
- Unit tests
- Monitoring setup

**Definition of Done:**
- [ ] Job runs successfully
- [ ] All clients processed
- [ ] Predictions stored correctly

---

#### [15B-009] A/B Test Framework (ML vs Rule-Based)

**Priority:** 🟡 HIGH  
**Effort:** 1.5 days  
**Assignee:** Data Scientist  
**Dependencies:** [15B-006]  
**Status:** Waiting for 15B-006

**Description:**
Set up A/B test to compare new ML model vs existing rule-based system.

**Acceptance Criteria:**
- [ ] Test design documented (hypothesis, metrics, duration)
- [ ] Random assignment: 50% to ML, 50% to rule-based
- [ ] Deterministic assignment (same client always gets same variant)
- [ ] Tracking: log which variant used for each prediction
- [ ] Statistical test: chi-square for conversion rate difference
- [ ] Winner determination logic (p-value < 0.05)
- [ ] Minimum sample size: 1,000 predictions per variant
- [ ] Test duration: 14 days minimum
- [ ] Dashboard showing real-time results
- [ ] Unit tests (>85% coverage)

**Test Hypothesis:**
- Null: ML model and rule-based have same conversion rate
- Alternative: ML model has higher conversion rate

**Metrics to Track:**
- Conversion rate (variant A vs B)
- Average probability score
- Confidence in prediction

**Deliverables:**
- A/B test code in `backend/analytics/ab_tester.py`
- Assignment logic
- Statistical test code
- Dashboard widget

**Definition of Done:**
- [ ] Test running
- [ ] Results tracking correctly
- [ ] Statistical calculations verified

---

### Sprint 2: Integration & Refinement (Oct 21-Nov 3)

#### [15B-010] Dashboard Widget for Explainability

**Priority:** 🟡 HIGH  
**Effort:** 1.5 days  
**Assignee:** Full-Stack Dev  
**Dependencies:** [15B-005], [15B-006]  
**Status:** Waiting for Sprint 2

**Description:**
Add explainability widget to internal_dashboard.html showing SHAP values and factors.

**Acceptance Criteria:**
- [ ] Feature importance bar chart (SHAP values)
- [ ] "Why is prediction 72%?" interactive section
- [ ] Factor contribution breakdown visualization
- [ ] Positive factors highlighted in green
- [ ] Negative factors highlighted in red
- [ ] Hover tooltips explaining each factor
- [ ] Responsive design for mobile dashboard
- [ ] Tests (>85% coverage)

---

#### [15B-011] Accuracy Tracking & Historical Comparison

**Priority:** 🟡 HIGH  
**Effort:** 1 day  
**Assignee:** Data Scientist  
**Dependencies:** [15B-008]  
**Status:** Waiting for Sprint 2

**Description:**
Track model accuracy over time and compare predictions to actual outcomes.

**Acceptance Criteria:**
- [ ] Monthly accuracy report generated
- [ ] Predictions vs actual outcomes visualization
- [ ] Accuracy trend over time (improving or degrading?)
- [ ] Identify which clients/segments have low accuracy
- [ ] Alert if accuracy drops below 65%
- [ ] Recommendations for model retraining
- [ ] Unit tests (>85% coverage)

---

#### [15B-012] Model Retraining Pipeline

**Priority:** 🟡 HIGH  
**Effort:** 1.5 days  
**Assignee:** ML Engineer  
**Dependencies:** [15B-004]  
**Status:** Waiting for Sprint 2

**Description:**
Automated pipeline to retrain model monthly with new data.

**Acceptance Criteria:**
- [ ] Scheduled monthly retraining (first Sunday of month)
- [ ] Collect new historical data (new predictions + outcomes)
- [ ] Re-run feature engineering on new data
- [ ] Train new model version
- [ ] Evaluate new model accuracy
- [ ] Compare to previous model
- [ ] If better: promote new model to production
- [ ] If worse: alert team, investigate why
- [ ] Model versioning: v1, v2, v3, etc.
- [ ] Fallback to previous model if issues

---

#### [15B-013] Unit Test Suite (>85% Coverage)

**Priority:** 🟡 HIGH  
**Effort:** 1.5 days  
**Assignee:** Data Scientist  
**Dependencies:** All components  
**Status:** Waiting for Sprint 2

**Description:**
Comprehensive unit tests for all ML components.

**Acceptance Criteria:**
- [ ] Test coverage >85% for all ML code
- [ ] Feature engineering tested
- [ ] Model inference tested
- [ ] SHAP calculation tested
- [ ] A/B test logic tested
- [ ] All edge cases covered
- [ ] CI/CD pipeline passing all tests

---

### Sprint 3: Production Ready (Nov 4-10)

#### [15B-014] Hyperparameter Tuning & Optimization

**Priority:** 🟡 HIGH  
**Effort:** 1 day  
**Assignee:** ML Engineer  
**Dependencies:** [15B-004]  
**Status:** Waiting for Sprint 3

**Description:**
Fine-tune model hyperparameters for better performance.

**Acceptance Criteria:**
- [ ] Expand GridSearch with more parameter combinations
- [ ] Genetic algorithm or Bayesian optimization (optional)
- [ ] Target accuracy >75%
- [ ] Evaluate on unseen test data
- [ ] Document best parameters found
- [ ] Update model with optimal params

---

#### [15B-015] Production Model Deployment & Serving

**Priority:** 🔴 CRITICAL  
**Effort:** 1 day  
**Assignee:** Full-Stack Dev  
**Dependencies:** [15B-012]  
**Status:** Waiting for Sprint 3

**Description:**
Deploy trained model to production with proper versioning and rollback.

**Acceptance Criteria:**
- [ ] Model served from disk with caching
- [ ] Model versioning: v1 → v2 (if improved)
- [ ] Graceful model loading (no downtime)
- [ ] Rollback procedure if new model has issues
- [ ] Monitoring: alert if model loading fails
- [ ] Performance: inference <500ms
- [ ] Scaling: handle 100+ concurrent requests

---

#### [15B-016] Monitoring & Alerting for Model Performance

**Priority:** 🟡 HIGH  
**Effort:** 1 day  
**Assignee:** Data Engineer  
**Dependencies:** [15B-011]  
**Status:** Waiting for Sprint 3

**Description:**
Set up monitoring dashboards and alerts for model performance.

**Acceptance Criteria:**
- [ ] Monitoring dashboard: accuracy, latency, throughput
- [ ] Alert if accuracy drops below 65%
- [ ] Alert if prediction latency exceeds 500ms
- [ ] Alert if error rate exceeds 1%
- [ ] Daily metrics report emailed to team
- [ ] Historical metrics visualization (30-day trend)
- [ ] Alerting integration with PagerDuty

---

## 📊 Summary by Sprint

| Sprint | Track A | Track B | Total |
|--------|---------|---------|-------|
| **Sprint 1** (Oct 7-20) | 8 tickets | 9 tickets | **17 tickets** |
| **Sprint 2** (Oct 21-Nov 3) | 5 tickets | 4 tickets | **9 tickets** |
| **Sprint 3** (Nov 4-10) | 3 tickets | 3 tickets | **6 tickets** |
| **TOTAL** | **16 tickets** | **16 tickets** | **32 tickets** |

---

## 🎯 Effort Estimation by Sprint

### Sprint 1 (Critical Path)

**Track A (Foundation):**
- 15A-001: 1d (setup)
- 15A-002: 2d (auth)
- 15A-003: 1d (redux)
- 15A-004: 1d (nav)
- 15A-005: 1.5d (websocket)
- 15A-006: 2d (dashboard)
- 15A-007: 1.5d (offline)
- 15A-008: 1d (performance)
**Track A Total: 11 days** (distributed: 2 devs × 5.5 days each)

**Track B (Foundation):**
- 15B-001: 1.5d (eda)
- 15B-002: 2d (features)
- 15B-003: 1.5d (training)
- 15B-004: 1d (evaluation)
- 15B-005: 1.5d (shap)
- 15B-006: 1.5d (api)
- 15B-007: 1d (database, parallel)
- 15B-008: 1.5d (batch)
- 15B-009: 1.5d (ab test)
**Track B Total: 13 days** (distributed: 4 devs × 3.25 days each)

**Sprint 1 Total: 24 days (11 + 13)**  
**With 8 developers: ~3 days per developer**

---

## 🚀 How to Use This Backlog

1. **Copy to Project Management System** (GitHub Projects, Jira, etc.)
2. **Assign developers** to each ticket
3. **Create git branches** matching ticket naming
4. **Sprint Planning (Mon Oct 7):**
   - Confirm team assignments
   - Discuss dependencies & risks
   - Set daily standup times
5. **Daily Standups:** Report progress and blockers
6. **Sprint Review (Fri Oct 18):** Demo completed work
7. **Sprint Retrospective:** What went well, what to improve

---

**Document Version:** 1.0  
**Created:** 2026-10-06 20:00 CLT  
**Status:** 🎯 READY FOR SPRINT 1 EXECUTION  
**Next Update:** After Sprint 1 completion (Oct 18, 2026)
