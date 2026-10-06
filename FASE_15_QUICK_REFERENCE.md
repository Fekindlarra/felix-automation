# FASE 15 Quick Reference
## One-Page Summary for Developers

**Project:** FASE 15: Mobile Apps + Advanced Predictions  
**Timeline:** Oct 7 - Nov 6, 2026 (5 weeks)  
**Status:** 🟢 Sprint 1 Ready (Oct 7-20)  
**Team:** 8 developers (4 Track A + 4 Track B)

---

## 📚 Documentation Hub

| What You Need | Where to Find It | Time |
|---------------|------------------|------|
| **I'm new, where do I start?** | [FASE_15_EXECUTION_FRAMEWORK.md](./FASE_15_EXECUTION_FRAMEWORK.md) | 15 min |
| **It's my first day (Oct 7)** | [FASE_15_DAY_1_CHECKLIST.md](./FASE_15_DAY_1_CHECKLIST.md) | 3.5 hrs |
| **I need to set up my dev environment** | [FASE_15_DEV_ENVIRONMENT_SETUP.md](./FASE_15_DEV_ENVIRONMENT_SETUP.md) | 1 hr |
| **I need a ticket to work on** | [FASE_15_INITIAL_TICKETS_BACKLOG.md](./FASE_15_INITIAL_TICKETS_BACKLOG.md) | 5 min search |
| **What's this sprint all about?** | [FASE_15_SPRINT_1_PLANNING.md](./FASE_15_SPRINT_1_PLANNING.md) | 20 min |
| **Why are we building this?** | [FASE_15_ROADMAP.md](./FASE_15_ROADMAP.md) | 15 min |

**👉 Start here if you're new:** [FASE_15_EXECUTION_FRAMEWORK.md](./FASE_15_EXECUTION_FRAMEWORK.md)

---

## 🎯 Sprint 1 Goals (Oct 7-20)

### Track A: Mobile Apps (React Native)
- ✅ iOS + Android apps running on simulators
- ✅ Real-time dashboard with WebSocket updates
- ✅ Offline capability with data sync
- ✅ 72% adoption baseline met

### Track B: ML Predictions
- ✅ ML model >70% accuracy
- ✅ Predictions API operational
- ✅ SHAP explainability working
- ✅ A/B testing framework built

**Success = Both tracks done, merged to `develop` by Oct 20** ✅

---

## 💻 Setup Commands (Copy & Paste)

### Track A - Mobile
```bash
cd /home/claude/felix-automation/frontend/mobile
npm install
npm start
# Press i (iOS simulator) or a (Android emulator)
```

### Track B - Predictions
```bash
cd /home/claude/felix-automation
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
jupyter lab
```

---

## 🔀 Git Workflow

```bash
# Start work on new ticket [15A-001]
git checkout -b feat/15a-001-auth-system

# Make commits with proper format
git commit -m "[15A-001] Implement biometric authentication

- Added react-native-biometrics integration
- Keychain storage for credentials
- JWT token refresh logic

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"

# Push and create PR
git push origin feat/15a-001-auth-system
# → Go to GitHub and create PR to develop branch
```

**Key Rules:**
- ✅ Always branch from `develop`
- ✅ PR title: `[TICKET-ID] Brief description`
- ✅ Require 2 reviewers before merge
- ✅ Keep commits small and focused
- ✅ Write tests alongside code (TDD)

---

## 📅 Weekly Schedule

| Day | Time | What |
|-----|------|------|
| **Mon-Thu** | 9am | Standup in #fase-15 |
| **Mon-Thu** | Anytime | Code, test, commit, review |
| **Friday** | 2pm CLT | Sprint review + weekly sync |

---

## 🚨 Blockers & Help

**Something's broken?**
→ Post to `#fase-15-blockers` immediately

**General question?**
→ Post to `#fase-15` channel

**Environment issue?**
→ Check [Dev Setup Troubleshooting](./FASE_15_DEV_ENVIRONMENT_SETUP.md#troubleshooting)

**Can't find a ticket?**
→ Browse [Backlog](./FASE_15_INITIAL_TICKETS_BACKLOG.md) and pick labeled "Sprint 1"

---

## 📊 Metrics That Matter

**Track A (Mobile):**
- App load time: <1.5s (on 4G)
- Test coverage: >85%
- iOS + Android both working

**Track B (Predictions):**
- Model accuracy: >70%
- Prediction latency: <500ms
- SHAP explanation: <1s

---

## 🏃 Day-to-Day Workflow

### Each Morning
```
1. `git pull origin develop` (get latest)
2. Check #fase-15-blockers (any overnight issues?)
3. Check your assigned ticket
4. Sync with your pod partner (2-person team)
```

### During Work
```
1. TDD: Write test first
2. Code: Make it pass
3. Commit: Often (1+ per day)
4. Push: Daily
5. Review: Ask pod partner
6. Merge: After approval
```

### Each Evening
```
1. Post standup update to #fase-15
2. Push all changes (even incomplete)
3. Flag blockers to #fase-15-blockers
4. Close VS Code with confidence 😊
```

---

## 🎬 Starting Your First Ticket

**Example: [15A-001] Setup React Native Project Scaffold**

```bash
# 1. Pick ticket from backlog (marked "Sprint 1", "15A-001")
# 2. Create branch
git checkout -b feat/15a-001-scaffold

# 3. Write test first (TDD)
# File: frontend/mobile/__tests__/setup.test.ts
// Test that Expo initializes

# 4. Make it pass (code)
# File: frontend/mobile/index.ts
// Setup Expo

# 5. Commit with format
git commit -m "[15A-001] Setup React Native project scaffold..."

# 6. Push to GitHub
git push origin feat/15a-001-scaffold

# 7. Create PR in GitHub (describe what you did)

# 8. Ask pod partner to review

# 9. Merge to develop (only after approval)
```

---

## ⚡ Performance Targets

| Metric | Target | Tool |
|--------|--------|------|
| App startup | <3s | React Native Debugger |
| Dashboard load | <1.5s | Network tab |
| Prediction latency | <500ms | FastAPI logs |
| SHAP calc | <1s | Python profiler |
| Build time | <3 min (React Native) | Terminal timer |
| Build time | <5 min (ML training) | Jupyter |

---

## 🔒 Code Quality Standards

Every commit should have:
- ✅ Tests (>85% coverage)
- ✅ Docstrings (functions, classes)
- ✅ No linting errors
  - Python: `pylint score > 9.0`
  - TypeScript: `eslint errors = 0`
- ✅ No security issues (`bandit` clean)
- ✅ Proper error handling

---

## 📱 Devices & Simulators

### Track A Developers
- **iOS:** Use simulator on Mac (Xcode installed)
- **Android:** Use emulator (Android Studio)
- **Test both:** Every PR must work on both

### Command to test
```bash
npm test           # Unit tests
npm start          # Start simulator
npm run ios        # iOS only
npm run android    # Android only
```

---

## 🐍 Python Dependencies (Track B)

Core ML libraries:
```
scikit-learn==1.3.0    # RandomForest classifier
pandas==2.0.0          # Data manipulation
numpy==1.24.0          # Numerical computing
shap==0.43.0           # Explainability
jupyter==1.0.0         # Notebooks
fastapi==0.104.0       # API server
asyncpg==0.28.0        # PostgreSQL async
```

Install all:
```bash
pip install -r requirements.txt
```

---

## 🎓 Training & Resources

**Git:**
- Cheat sheet: `git` [Pro Git Book](https://git-scm.com/book)

**React Native:**
- Docs: [React Native Official](https://reactnative.dev)
- Navigation: [React Navigation](https://reactnavigation.org)

**Machine Learning:**
- Scikit-learn: [Official Docs](https://scikit-learn.org)
- SHAP: [GitHub](https://github.com/shap/shap)

**FastAPI:**
- Tutorial: [FastAPI Official](https://fastapi.tiangolo.com)

---

## 🏁 Sprint 1 Finish Line (Oct 20)

By end of Sprint 1, we should have:

✅ **Track A:**
- Code in `feat/15a-*` branches → Pull request → Merged to develop
- Both simulators running
- Biometric auth working
- Redux store operational
- WebSocket client connected
- Offline mode functional

✅ **Track B:**
- Code in `feat/15b-*` branches → Pull request → Merged to develop
- EDA complete
- Feature engineering done
- Model trained and validated
- Predictions API responding
- SHAP explanations working
- A/B test framework built

✅ **Everyone:**
- CI/CD passing (GitHub Actions)
- Code review completed
- Tests passing (>85% coverage)
- Documentation updated

---

## 📞 Emergency Contacts

| Situation | Channel | Response Time |
|-----------|---------|----------------|
| **Critical Blocker** | #fase-15-blockers | <15 min |
| **General Question** | #fase-15 | <1 hour |
| **Code Review** | PR comment | <4 hours |
| **Infrastructure Issue** | #fase-15-devops | <30 min |

---

## 🎉 You're Ready!

**You have everything you need to start Sprint 1 on October 7.**

1. Read [FASE_15_EXECUTION_FRAMEWORK.md](./FASE_15_EXECUTION_FRAMEWORK.md)
2. Join Slack channels (#fase-15, #fase-15-blockers)
3. Complete [Dev Environment Setup](./FASE_15_DEV_ENVIRONMENT_SETUP.md)
4. Attend kickoff meeting at 9am CLT
5. Follow [Day 1 Checklist](./FASE_15_DAY_1_CHECKLIST.md)
6. Pick first ticket and start coding
7. Commit, push, create PR, repeat 🔄

**Questions before Oct 7?** Post in #fase-15 channel.

---

**Last Updated:** October 6, 2026  
**Next Update:** October 7, 2026 (after kickoff)  
**Maintained By:** Claude Code (autonomous agent)
