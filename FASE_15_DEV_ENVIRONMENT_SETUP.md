# FASE 15 - Development Environment & Git Strategy

**Date:** 2026-10-06  
**Status:** 🚀 READY FOR TEAM SETUP  
**Document Purpose:** Setup instructions for all 8 developers (both tracks)

---

## Part 1: Git Repository Structure & Branching

### Repository Setup (Central)

```bash
# Repository: https://github.com/enbuenamesa/felix-automation
# Default branch: main (production v14.0.0)
# Development branch: develop (integration point for FASE 15)

# Current state:
# main          → v14.0.0 (PHASE 14 DEPLOYED - STABLE ✅)
# develop       → Ready for FASE 15 features
# stage         → Staging environment (for testing before production)
```

### Branch Structure for FASE 15

```
MAIN BRANCHES (Protected)
├── main (production, v14.0.0) ← only merge from stage via PR
├── stage (staging)            ← only merge from develop via PR
└── develop (integration)      ← feature PRs merge here

FEATURE BRANCHES (Track A: Mobile)
├── feat/mobile-core-setup     ← React Native scaffold, nav, redux
├── feat/mobile-auth           ← Biometric + password auth
├── feat/mobile-websocket      ← WebSocket + real-time updates
├── feat/mobile-dashboard      ← DashboardScreen component
├── feat/mobile-offline        ← AsyncStorage + sync queue
├── feat/mobile-predictions    ← PredictionsScreen + details
├── feat/mobile-push-notifs    ← Push notification system
└── feat/mobile-polish         ← UI/UX refinement, animations

FEATURE BRANCHES (Track B: Predictions)
├── feat/ml-data-pipeline      ← EDA, data preparation
├── feat/ml-feature-eng        ← Feature engineering pipeline
├── feat/ml-model-train        ← Model training & validation
├── feat/ml-explainability     ← SHAP integration
├── feat/ml-api                ← Predictions API endpoints
├── feat/ml-database           ← Schema updates for predictions
├── feat/ml-batch-jobs         ← Scheduled batch predictions
└── feat/ml-abtesting          ← A/B testing framework

BUGFIX BRANCHES (As needed)
└── bugfix/category-name       ← Any hotfixes discovered during dev
```

---

## Part 2: Git Workflow (All Developers)

### Initial Setup (First-time only)

```bash
# 1. Clone the repository
git clone https://github.com/enbuenamesa/felix-automation.git
cd felix-automation

# 2. Verify remotes
git remote -v
# Output:
# origin    https://github.com/enbuenamesa/felix-automation.git (fetch)
# origin    https://github.com/enbuenamesa/felix-automation.git (push)

# 3. Fetch all branches
git fetch origin

# 4. Checkout develop (integration branch)
git checkout develop
git pull origin develop

# 5. Create local tracking branches (optional but recommended)
git checkout -b track-a origin/feat/mobile-core-setup   # Mobile devs
git checkout -b track-b origin/feat/ml-data-pipeline    # ML devs
```

### Daily Workflow

**At the start of your day:**
```bash
# 1. Switch to your feature branch
git checkout feat/mobile-auth  # or your assigned branch

# 2. Pull latest changes from remote
git pull origin feat/mobile-auth

# 3. Sync with develop (to catch other team's changes)
git fetch origin develop
git rebase origin/develop
# If conflicts arise, resolve them and:
git rebase --continue
```

**During development:**
```bash
# Make changes to files
code src/screens/LoginScreen.tsx

# Stage your changes
git add src/screens/LoginScreen.tsx
# or stage all changes
git add .

# Commit with descriptive message
git commit -m "feat: Add biometric authentication to LoginScreen

- Integrate react-native-biometrics library
- Add biometric prompt after password entry
- Fallback to password-only on unsupported devices
- Add unit tests for biometric flow

Closes #123"

# View your commits before pushing
git log --oneline -5

# Push to remote
git push origin feat/mobile-auth
```

**Commit Message Format:**
```
<type>(<scope>): <subject>

<body>

<footer>

Types: feat, fix, docs, style, refactor, test, chore
Scope: mobile, predictions, database, api, etc.
Subject: imperative, lowercase, no period, max 50 chars
Body: explain what and why, not how (wrap at 72 chars)
Footer: "Closes #123" or "Refs #456"

Examples:
- feat(mobile): Add biometric authentication
- fix(predictions): Handle null confidence scores
- docs(api): Add WebSocket endpoint documentation
- test(ml): Add RandomForest model unit tests
```

### Pull Request Workflow

**Creating a PR:**
```bash
# 1. Push your feature branch
git push origin feat/mobile-auth

# 2. Go to GitHub → felix-automation repository
# 3. Click "Compare & pull request" or "New pull request"
# 4. Configure PR:
#    - Base: develop (not main!)
#    - Compare: feat/mobile-auth
#    - Title: [15A-002] Implement biometric authentication
#    - Description (from template):

---
## 📋 Description
Brief summary of changes.

## 🎯 Related Issue
Closes #123

## ✅ Checklist
- [ ] Tests added/updated (>85% coverage)
- [ ] Code review requested
- [ ] No breaking changes
- [ ] Documentation updated
- [ ] All CI checks passing

## 📊 Metrics
- Lines added: 150
- Files changed: 3
- Test coverage: 87%

---

# 5. Request reviewers (Track Lead for your track)
# 6. Address review feedback:

git add .
git commit -m "review: Address feedback from @lead-dev"
git push origin feat/mobile-auth

# 7. After approval, merge to develop
# (Usually done by Track Lead or automated)
```

**Code Review Process (Track Leads):**
```bash
# 1. Receive PR notification in Slack
# 2. Review code on GitHub:
#    - Check logic and design
#    - Verify tests (>85% coverage)
#    - Run locally if needed:

git fetch origin feat/mobile-auth
git checkout -b review/mobile-auth origin/feat/mobile-auth
npm install
npm test
npm start

# 3. Comment on PR or approve
# 4. If approved, merge:

git checkout develop
git pull origin develop
git merge origin/feat/mobile-auth
git push origin develop
# OR click "Merge pull request" on GitHub
```

### Weekly Integration (Every Friday)

```bash
# TRACK A LEAD (Friday 4pm CLT)
git checkout develop
git pull origin develop
# Verify all Track A PRs merged
git branch -r | grep feat/mobile-

# TRACK B LEAD (Friday 4pm CLT)
git checkout develop
git pull origin develop
# Verify all Track B PRs merged
git branch -r | grep feat/ml-

# INTEGRATION LEAD (Friday 5pm CLT)
# Merge develop → stage for weekend testing
git checkout stage
git pull origin stage
git merge origin/develop
git push origin stage
# Announce: "develop merged to stage for testing"

# Status check (Monday 9am CLT)
# Verify stage deployment is stable
# If yes → ready for next week
# If issues → hotfix in develop, retry merge
```

### Monthly Production Deployment (If approved)

```bash
# Prerequisites:
# - Stage environment tested for 1+ week
# - All stakeholder sign-offs collected
# - Deployment checklist completed

# PRODUCTION LEAD
git checkout main
git pull origin main
git merge origin/stage
git push origin main
git tag -a v15.0.0 -m "FASE 15 Release"
git push origin v15.0.0

# Trigger production deployment (if CI/CD automated)
# Manual deployment steps in DEPLOYMENT_GUIDE.md
```

---

## Part 3: Local Development Environment Setup

### Prerequisites

**System Requirements:**
- macOS 12+, Ubuntu 20.04+, or Windows 10+
- 8GB RAM minimum (16GB recommended)
- 50GB free disk space
- Git 2.30+

**Tools Installation:**

```bash
# macOS (via Homebrew)
brew install python@3.11 node@18 postgresql sqlite3 redis

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv nodejs postgresql sqlite3 redis-server

# Windows (via Chocolatey)
choco install python nodejs sqlite postgresql redis
```

---

### Backend Setup (All Developers)

```bash
# 1. Create Python virtual environment
cd felix-automation
python3.11 -m venv venv

# 2. Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file for development
cat > .env << 'EOF'
# Development Environment
ENVIRONMENT=development
DEBUG=True

# Database
DATABASE_URL=sqlite:///felix_dev.db

# Security
SECRET_KEY=dev-secret-key-change-in-production
JWT_EXPIRATION_HOURS=24
FERNET_KEY=your-fernet-key-here

# Shopify (Mock for dev)
SHOPIFY_API_KEY=mock-key-dev
SHOPIFY_API_SECRET=mock-secret-dev

# SendGrid (Mock for dev)
SENDGRID_API_KEY=mock-key-dev

# Redis (if using)
REDIS_URL=redis://localhost:6379/0

# WebSocket
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_MOBILE_HEARTBEAT_INTERVAL=60

# Logging
LOG_LEVEL=DEBUG
EOF

# 6. Initialize database
python backend/init_database.py

# 7. Run backend server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

Access:
- API: http://localhost:8000/docs (Swagger UI)
- WebSocket: ws://localhost:8000/ws
- Dashboards: http://localhost:8000/internal_dashboard.html

---

### Mobile Development Setup (Track A Developers)

```bash
# 1. Navigate to mobile directory
cd mobile

# 2. Install Node dependencies
npm install

# 3. Create .env file for mobile
cat > .env << 'EOF'
BACKEND_URL=http://localhost:8000
WEBSOCKET_URL=ws://localhost:8000
API_VERSION=v14
ENVIRONMENT=development
EOF

# 4. Option A: Using Expo (Recommended for rapid dev)
npm install -g eas-cli
eas init  # Initialize EAS project (one-time)

# 5. Start development server
npm start

# iOS Development:
# - Press 'i' in terminal → iOS Simulator opens
# - Or scan QR code with Expo Go app on iPhone

# Android Development:
# - Press 'a' in terminal → Android Emulator opens
# - Or scan QR code with Expo Go app on Android

# 6. Install development tools
# For debugging:
npm install --save-dev @react-native/debugger

# Run tests:
npm test

# Lint code:
npm run lint

# Format code:
npm run format
```

**Environment Files:**
```
mobile/
├── .env                    # Development secrets (git-ignored)
├── .env.example            # Template for others
├── app.json                # Expo config
├── eas.json                # EAS build config
├── tsconfig.json           # TypeScript config
├── jest.config.js          # Test config
└── .eslintrc.json          # Linting config
```

**First Run Checklist:**
- [ ] `npm install` completes without errors
- [ ] `npm start` shows dev server running
- [ ] iOS Simulator or Android Emulator starts
- [ ] "Hello World" screen visible in app
- [ ] `npm test` runs without errors

---

### ML/Data Science Setup (Track B Developers)

```bash
# 1. Create Python virtual environment (separate from backend)
python3.11 -m venv venv-ml
source venv-ml/bin/activate  # or venv-ml\Scripts\activate on Windows

# 2. Install ML dependencies
pip install -r requirements-ml.txt
# Contains: pandas, numpy, scikit-learn, shap, jupyterlab, etc.

# 3. Create notebooks directory
mkdir -p notebooks
cd notebooks

# 4. Start Jupyter Lab (for EDA & experimentation)
jupyter lab

# Opens at http://localhost:8888

# 5. Create new notebook: data_exploration.ipynb
# Start with:
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Load historical data from FASE 14
df = pd.read_sql("SELECT * FROM predictions LIMIT 100", con="sqlite:///../felix_dev.db")
print(df.head())
```

**Directory Structure:**
```
backend/
├── analytics/
│   ├── ml_pipeline.py         # ML model + training
│   ├── explainability.py      # SHAP integration
│   └── feature_engineering.py # Feature preprocessing
├── models/
│   └── conversion_predictor_v1.pkl  # Trained model (git-ignored)
└── tests/
    ├── test_ml_pipeline.py
    ├── test_explainability.py
    └── test_feature_engineering.py

notebooks/
├── 01_eda.ipynb               # Exploratory Data Analysis
├── 02_feature_engineering.ipynb  # Feature creation
├── 03_model_training.ipynb    # Model training & validation
└── 04_shap_explainability.ipynb  # Explainability analysis
```

---

### Database Setup (All Developers)

```bash
# 1. Create development database (SQLite)
python backend/init_database.py --reset

# Output: "Database reset successfully at felix_dev.db"

# 2. Verify tables created
sqlite3 felix_dev.db ".tables"

# Expected output: Shows all tables including new ones:
# prediction_history, ab_tests, ab_test_results, etc.

# 3. Seed with sample data (optional)
python backend/seed_database.py

# 4. Inspect schema
sqlite3 felix_dev.db ".schema prediction_history"

# Output: Shows columns for predictions
```

---

### Docker Setup (Optional, for production-like environment)

```bash
# 1. Install Docker & Docker Compose
# macOS: brew install docker docker-compose
# Ubuntu: sudo apt-get install docker.io docker-compose
# Windows: Install Docker Desktop

# 2. Build Docker image
docker build -t felix-automation:latest .

# 3. Run with docker-compose
docker-compose up -d

# Services started:
# - FastAPI backend: http://localhost:8000
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379

# 4. View logs
docker-compose logs -f backend

# 5. Stop services
docker-compose down
```

---

### IDE Setup & Recommended Extensions

**VS Code (Recommended)**

```json
// .vscode/settings.json (project-specific)
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python"
  },
  "[javascript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true
  }
}
```

**Recommended Extensions:**
- `ms-python.python` - Python extension
- `ms-python.vscode-pylance` - Type checking
- `ms-python.debugpy` - Python debugging
- `esbenp.prettier-vscode` - Code formatter
- `dbaeumer.vscode-eslint` - ESLint
- `github.copilot` - AI code completion
- `REST Client` - Test API endpoints
- `Thunder Client` - API testing (lightweight)

**PyCharm (Alternative)**
- Python/Flask support built-in
- Strong debugging & profiling tools
- Remote Python interpreter support

---

## Part 4: CI/CD Pipeline & Automated Checks

### GitHub Actions Setup

```yaml
# .github/workflows/tests.yml
name: Tests & Linting

on:
  push:
    branches: [develop, main, stage]
  pull_request:
    branches: [develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=backend --cov-report=xml
      - run: pylint backend/ --exit-zero
      
  mobile-tests:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd mobile && npm ci
      - run: npm test -- --coverage
      - run: npm run lint

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install bandit
      - run: bandit -r backend/ --exit-zero
```

### Local Pre-commit Hooks

```bash
# 1. Install pre-commit framework
pip install pre-commit

# 2. Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/pylint
    rev: v2.17.4
    hooks:
      - id: pylint

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.40.0
    hooks:
      - id: eslint
        files: mobile/
        types: [javascript, tsx]
EOF

# 3. Install hooks
pre-commit install

# 4. Run hooks on changed files
# (Automatically runs on git commit)
```

---

## Part 5: Development Checklist

### Before Starting Sprint 1

**Each Developer (individually):**
- [ ] Clone repository and checkout develop
- [ ] Set up Python/Node environments
- [ ] Run tests locally (should all pass)
- [ ] Verify IDE setup
- [ ] Add SSH key to GitHub (if not done)
- [ ] Join Slack channel #fase-15

**Track A Lead:**
- [ ] Create git branches for all mobile tickets
- [ ] Set up React Native project scaffold
- [ ] Create initial PR template for mobile
- [ ] Schedule daily standups (9am CLT, 15 min)

**Track B Lead:**
- [ ] Create git branches for all ML tickets
- [ ] Set up Jupyter notebooks environment
- [ ] Prepare sample data for EDA
- [ ] Schedule daily standups (9am CLT, 15 min)

**Integration Lead:**
- [ ] Verify CI/CD pipeline is working
- [ ] Test deployment to staging
- [ ] Create Slack notification webhooks
- [ ] Set up monitoring dashboards

### Daily Standup Format (15 min, Slack thread)

```
🏃 <Name> Status Update (Day N):

✅ Yesterday:
- Completed auth login screen
- Merged PR #456 to develop

🔄 Today:
- Implement biometric prompt
- Write unit tests for LoginScreen

🚧 Blockers:
- None

📊 Metrics:
- LOC added: 150
- Tests added: 5
- Coverage: 87%
```

---

## Part 6: Communication & Escalation

### Slack Channels

```
#fase-15                    Main channel for all announcements
#fase-15-mobile             Track A discussions (TRACK A LEADS: post daily standup here)
#fase-15-predictions        Track B discussions (TRACK B LEADS: post daily standup here)
#fase-15-devops             CI/CD, deployment, infrastructure
#fase-15-blockers           Emergency issues requiring immediate attention
```

### Escalation Path

```
Issue discovered
  ↓
1. Try to resolve locally (ask team on Slack)
  ↓
2. If can't resolve → escalate to Track Lead
  ↓
3. If Track Lead can't resolve → escalate to Integration Lead
  ↓
4. If still blocking → emergency call with both Track Leads + Integration Lead
```

---

## Part 7: Quick Reference Commands

### Git Commands

```bash
# Check status
git status

# Create & checkout branch
git checkout -b feat/mobile-auth

# Stage changes
git add src/screens/LoginScreen.tsx
git add .  # All files

# Commit
git commit -m "feat(mobile): Add biometric auth"

# Push
git push origin feat/mobile-auth

# Update from remote
git pull origin develop

# Sync with develop (if behind)
git fetch origin develop
git rebase origin/develop

# View commits
git log --oneline -10

# Undo last commit (before push)
git reset --soft HEAD~1

# Force push (use carefully, only on feature branches)
git push -f origin feat/mobile-auth
```

### Backend Commands

```bash
# Run server
cd backend
uvicorn main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Lint
pylint backend/

# Format code
black backend/

# Database
python init_database.py --reset
sqlite3 felix_dev.db ".tables"
```

### Mobile Commands

```bash
# Start dev server
cd mobile
npm start

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Lint
npm run lint

# Format
npm run format

# Build for iOS
eas build --platform ios

# Build for Android
eas build --platform android
```

---

## Part 8: Troubleshooting

### Common Issues & Solutions

**Python: "No module named 'xyz'"**
```bash
# Solution: Ensure venv is activated and requirements installed
source venv/bin/activate
pip install -r requirements.txt
```

**Node: "npm ERR! ERESOLVE unable to resolve dependency tree"**
```bash
# Solution: Clean install
rm package-lock.json node_modules -rf
npm install
```

**Git: "fatal: refusing to merge unrelated histories"**
```bash
# Solution: Pull with allow-unrelated-histories
git pull origin develop --allow-unrelated-histories
```

**Database: "sqlite3 database is locked"**
```bash
# Solution: Close other connections and reset
rm felix_dev.db
python backend/init_database.py
```

**Port already in use (port 8000, 3000, etc.)**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

---

**Document Version:** 1.0  
**Created:** 2026-10-06 19:45 CLT  
**Status:** 🚀 READY FOR TEAM ONBOARDING  
**Last Updated:** 2026-10-06
