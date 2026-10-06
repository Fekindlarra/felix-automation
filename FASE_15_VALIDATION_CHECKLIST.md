# FASE 15 Validation Checklist

**Status:** Sprint 1 Code Generation Complete ✅  
**Date:** October 6, 2026  
**Target:** Validate both tracks (A & B) are functioning locally

---

## 📋 Pre-Flight Checklist

### Requirements
- [ ] Python 3.11+ installed
- [ ] Node.js 20+ installed (for React Native)
- [ ] npm or yarn package manager
- [ ] Git (for version control)
- [ ] Xcode (macOS only, for iOS simulator) OR Android Studio (for Android simulator)

### Environment Setup
```bash
# Clone/check project exists
cd /home/claude/felix-automation

# Verify git is initialized (optional, for tracking changes)
git status

# Create .env file for backend
cp .env.example .env
# Edit .env with your local settings (use defaults for development)
```

---

## 🎯 Phase 1: Track B Validation (Python ML Backend) - 45 min

### Step 1.1: Install Backend Dependencies (5 min)
```bash
# Navigate to project root
cd /home/claude/felix-automation

# Install Python dependencies for FASE 15
pip install -r requirements-fase15.txt

# Verify installation
pip list | grep -E "fastapi|pytest|scikit-learn|shap"
# Should show: fastapi, pytest, scikit-learn, shap, sqlalchemy, pydantic, jwt
```

**Expected Output:**
```
fastapi==0.104.1
pytest==7.4.3
scikit-learn==1.3.2
shap==0.43.0
sqlalchemy==2.0.23
pydantic==2.5.0
PyJWT==2.8.1
```

### Step 1.2: Start Backend API (10 min)
```bash
# Navigate to API directory
cd backend/api

# Run the FastAPI server
python main.py

# Expected output:
# 🚀 FASE 15 API Starting (Track B - ML Predictions)
# ✅ Database initialized
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

**Keep this terminal open** - you'll test it from another terminal

### Step 1.3: Verify API Health (10 min)

**In a NEW terminal window:**
```bash
# Check health endpoint
curl http://localhost:8000/api/health

# Expected response:
# {"status":"🟢 healthy","version":"1.0.0","environment":"development"}
```

✅ **Verification:** Status should show "🟢 healthy"

### Step 1.4: View API Documentation (5 min)

**In browser:**
```
http://localhost:8000/docs
```

You should see:
- ✅ Swagger UI showing all endpoints
- ✅ Sections: authentication, predictions, events, websocket
- ✅ Health check endpoint
- ✅ Info endpoint listing features

✅ **Verification:** Swagger docs load without errors

### Step 1.5: Test Prediction Endpoint (10 min)

**In terminal:**
```bash
# Test a sample prediction
curl -X POST http://localhost:8000/api/predictions/generate \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test_client_001",
    "web_score": 75,
    "facebook_score": 85,
    "google_score": 80,
    "business_type": "ecommerce",
    "company_size": "pyme"
  }'

# Expected response (pretty-printed):
# {
#   "client_id": "test_client_001",
#   "probability": 78.5,
#   "confidence": 0.89,
#   "risk_factors": [],
#   "positive_factors": ["Strong web presence", "Good social engagement"],
#   "shap_explanations": [
#     {"feature_name": "web_score", "impact": 0.45, "direction": "positive"},
#     ...
#   ],
#   "predicted_timeline_days": 14
# }
```

✅ **Verification:** Response includes probability, confidence, and SHAP explanations

### Step 1.6: Test Health Check via Pytest (5 min)

**In new terminal:**
```bash
cd backend/api

# Run auth tests
pytest tests/test_auth.py -v

# Expected output:
# test_auth.py::test_health_check PASSED
# test_auth.py::test_login_invalid_credentials PASSED  
# test_auth.py::test_biometric_login PASSED
# ======================== 3 passed in 0.23s ========================
```

✅ **Verification:** All 3 tests pass

### Step 1.7: Test Predictions via Pytest (5 min)

```bash
# Run prediction tests
pytest tests/test_predictions.py -v

# Expected output:
# test_predictions.py::test_generate_prediction_valid PASSED
# test_predictions.py::test_generate_prediction_low_scores PASSED
# test_predictions.py::test_shap_explanations_present PASSED
# ======================== 3 passed in 0.45s ========================
```

✅ **Verification:** All 3 prediction tests pass

### Step 1.8: Check Code Coverage (5 min)

```bash
# Run all tests with coverage
cd backend/api
pytest tests/ -v --cov=. --cov-report=html

# Generate report
ls -la htmlcov/

# View report (optional - requires browser)
# open htmlcov/index.html
```

✅ **Verification:** Coverage report shows >85% code coverage

---

## 📱 Phase 2: Track A Validation (React Native Mobile) - 30 min

**Keep the backend running from Phase 1!** (in separate terminal)

### Step 2.1: Install Mobile Dependencies (10 min)

```bash
# Navigate to frontend
cd frontend/mobile

# Install npm dependencies
npm install

# Expected output:
# added XXX packages in XXs
# ✅ All dependencies installed successfully
```

**Common Issues:**
- If you get "permission denied": Try `sudo npm install -g expo-cli`
- If node_modules fails: Try `npm ci` (clean install)

### Step 2.2: Start Expo Development Server (5 min)

```bash
# From frontend/mobile directory, start Expo
npm start

# Expected output:
# ███████████████ Expo CLI starting... ███████████████
# Starting Expo CLI...
# 
# ✅ Your project is ready!
# 
# Android app: Press a
# iOS app:    Press i
# Web:        Press w
# Reset:      Press r
```

**Keep this running** - don't close this terminal

### Step 2.3: Launch iOS Simulator (iOS users - 10 min)

**In new terminal (leave npm start running):**

```bash
# Install Xcode Command Line Tools (if needed)
xcode-select --install

# From the Expo terminal above, press 'i'
# Should open iOS Simulator with the app loading

# Expected to see:
# ✅ Loading app bundle
# ✅ App starts with login screen
# ✅ Two input fields (email, password)
# ✅ Login button
# ✅ Biometric authentication button (Face ID / Touch ID)
```

**If simulator doesn't open:**
```bash
# Manually open simulator
open -a Simulator

# Then try npm start again
npm start
# Press 'i'
```

✅ **Verification:** See login screen with email/password fields

### Step 2.4: Launch Android Emulator (Android users - 10 min)

**Requirements:** Android Studio installed and emulator configured

```bash
# From Android Studio, start an emulator
# Then from Expo terminal, press 'a'

# Expected to see:
# ✅ Loading app bundle  
# ✅ App starts with login screen
# ✅ Same login fields and buttons
```

✅ **Verification:** See login screen on Android emulator

### Step 2.5: Test Biometric Authentication (Optional - 5 min)

```
On iOS Simulator:
- Tap "Use Biometrics" button
- In Simulator menu: Device → Biometric → Enrolled (or matching)
- Simulator will auto-approve biometric auth
- Expected: Should attempt login

On Android Emulator:
- Tap "Use Biometrics" button
- App attempts biometric auth
- Result depends on emulator capabilities
```

✅ **Verification:** Biometric button is clickable and responds

### Step 2.6: Run Mobile Tests (5 min)

**In new terminal (keep app running):**

```bash
cd frontend/mobile

# Run Jest tests
npm run test:coverage

# Expected output:
# PASS  src/services/api.test.ts
# PASS  src/services/websocket.test.ts
# PASS  src/screens/AuthScreen.test.tsx
#
# Test Suites: 3 passed, 3 total
# Tests:       12 passed, 12 total  
# Coverage: 87% Statements, 85% Branches
```

✅ **Verification:** Tests pass with >85% coverage

### Step 2.7: TypeScript Type Checking (5 min)

```bash
# Type check the TypeScript code
npm run type-check

# Expected output:
# ✅ No TypeScript errors found
# Type checking complete
```

✅ **Verification:** No TypeScript compilation errors

### Step 2.8: ESLint Linting (5 min)

```bash
# Run linter
npm run lint

# Expected output:
# ✅ No linting errors
```

✅ **Verification:** No linting errors or warnings

---

## 🔌 Phase 3: Integration Validation (WebSocket Real-Time) - 15 min

**Requirements:** Both Track A and Track B running

### Step 3.1: Test WebSocket Connection (10 min)

**In new terminal:**

```bash
# Test WebSocket stats endpoint
curl http://localhost:8000/api/ws/stats

# Expected response:
# {
#   "total_connections": 0,
#   "unique_clients": 0,
#   "connections": []
# }
```

✅ **Verification:** WebSocket endpoint is responding

### Step 3.2: Broadcast Test Event (5 min)

```bash
# Send a test prediction event
curl -X POST http://localhost:8000/api/ws/test-broadcast \
  -H "Content-Type: application/json" \
  -d '{"client_id": "test_client"}'

# Expected response:
# {"status":"test message sent"}
```

✅ **Verification:** Broadcast endpoint is functional

### Step 3.3: Manual WebSocket Connection (Optional - 10 min)

If you want to manually test WebSocket:

```bash
# Install websocat (WebSocket client)
# macOS: brew install websocat
# Linux: Install via package manager
# Windows: Download from GitHub

# Connect to WebSocket
websocat ws://localhost:8000/ws/predictions/user_001/client_001?token=test_token

# You should see:
# {"type":"connection_confirmed","connection_id":"...","timestamp":"..."}

# Type this to subscribe to events:
# {"type":"subscribe","client_ids":["client_001"]}

# Expected:
# {"type":"subscription_updated","subscribed_to":["client_001"],...}

# Type 'ping' to test heartbeat:
# {"type":"ping"}

# Expected response:
# {"type":"pong","timestamp":"..."}
```

✅ **Verification:** WebSocket connection works and responds to messages

---

## ✅ Validation Summary

### Track B (Backend) Checklist
- [ ] Dependencies installed (pip list shows all packages)
- [ ] Server starts without errors (`🚀 FASE 15 API Starting`)
- [ ] Database initializes (`✅ Database initialized`)
- [ ] Health check responds (`🟢 healthy`)
- [ ] Swagger docs load (`http://localhost:8000/docs`)
- [ ] Prediction endpoint returns probability + SHAP (curl test)
- [ ] Auth tests pass (pytest test_auth.py)
- [ ] Prediction tests pass (pytest test_predictions.py)
- [ ] Code coverage >85% (pytest --cov)
- [ ] WebSocket stats endpoint works

### Track A (Mobile) Checklist
- [ ] Dependencies installed (npm install completes)
- [ ] Expo development server starts (`npm start`)
- [ ] iOS Simulator shows login screen (press 'i')
- [ ] OR Android Emulator shows login screen (press 'a')
- [ ] Biometric auth button is present
- [ ] Jest tests pass (`npm run test:coverage`)
- [ ] TypeScript type checking passes (`npm run type-check`)
- [ ] Linting passes (`npm run lint`)

### Integration Checklist
- [ ] Both Track A and Track B running simultaneously
- [ ] WebSocket `/api/ws/stats` endpoint responds
- [ ] Test broadcast works (`/api/ws/test-broadcast`)
- [ ] WebSocket can establish connections (optional manual test)

---

## 🐛 Troubleshooting

### Backend Issues

**"ModuleNotFoundError: No module named 'fastapi'"**
```bash
pip install -r requirements-fase15.txt
```

**"Port 8000 already in use"**
```bash
# Find and kill process on port 8000
lsof -i :8000
# Get the PID, then:
kill -9 <PID>
```

**"SQLite database locked"**
```bash
cd backend/api
rm fase15.db
python main.py  # Recreates database
```

**"ImportError: cannot import name 'database'"**
- Make sure you're in the correct directory
- Check that `backend/api/database.py` exists
- Verify Python path includes `backend/api/`

### Frontend Issues

**"expo-cli not found"**
```bash
npm install -g expo-cli
```

**"Simulator won't start"**
```bash
# iOS: Make sure Xcode is installed
xcode-select --install

# Android: Open Android Studio, create/start an emulator
# Then run: npm start and press 'a'
```

**"Module not found: '@services/api'"**
```bash
# Path aliases not working - reinstall
rm -rf node_modules package-lock.json
npm install
```

**"Jest tests failing"**
```bash
# Clear Jest cache
npm run test:coverage -- --clearCache
npm run test:coverage
```

### WebSocket Issues

**"WebSocket connection refused"**
- Ensure backend is running: `python main.py` shows "Uvicorn running"
- Check port 8000 is open: `curl http://localhost:8000/api/health`
- Check firewall allows localhost:8000

**"Connection times out"**
- Backend might be using different port (check console output)
- Try accessing directly: `http://localhost:8000/docs`

---

## 📞 Next Steps After Validation

1. **If all checks pass** ✅
   - Create initial git commits: `git add . && git commit -m "FASE 15: Sprint 1 Code Generation Complete"`
   - Push to repository
   - Proceed to Phase 2: WebSocket real-time integration
   - Begin ML model training with actual FASE 14 data

2. **If checks fail** ❌
   - Note which step failed
   - Check troubleshooting section
   - Contact Claude for debugging

3. **Performance Notes**
   - Track A app startup should be <3 seconds
   - Track B health check should respond <100ms
   - Dashboard load time target: <1.5s on 4G

---

## 📊 Success Criteria

**Validation is COMPLETE when:**
- ✅ Track B: All 10 bullet points checked
- ✅ Track A: All 8 bullet points checked
- ✅ Integration: All 3 bullet points checked
- ✅ No major errors or warnings
- ✅ Both servers can run simultaneously
- ✅ API responds to requests
- ✅ Mobile app displays login screen
- ✅ Tests pass with >85% coverage

---

**Estimated Total Time:** 90 minutes (45 min Track B + 30 min Track A + 15 min Integration)

**Generated:** October 6, 2026  
**By:** Claude Haiku 4.5  
**Session:** https://claude.ai/code/session_01EZEKRd8BUbc4mh5jQNB73m
