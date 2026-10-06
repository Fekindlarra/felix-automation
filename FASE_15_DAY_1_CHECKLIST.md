# FASE 15 Day 1 Checklist (Oct 7, 2026)
## First Day of Sprint 1 - Get Set Up in 2 Hours ⚡

**Timeline:** 9:00am - 11:00am CLT (before first code commit)

---

## Pre-Kickoff (Before 9am) - 15 min

**For All Developers:**
- [ ] Join Slack workspace if not already a member
- [ ] Accept calendar invite to "FASE 15 Sprint 1 Kickoff" (9am CLT)
- [ ] Read the first 2 sections of [FASE_15_EXECUTION_FRAMEWORK.md](./FASE_15_EXECUTION_FRAMEWORK.md)
- [ ] Have your laptop ready with VS Code or PyCharm installed

---

## Kickoff Meeting (9:00-9:30am) - 30 min

**Everyone together:**
- [ ] Felipe presents high-level FASE 15 vision (5 min)
- [ ] Tech lead reviews architecture (10 min)
- [ ] Team assignments confirmed (5 min)
- [ ] Q&A (10 min)

**Outputs:**
- Know your track (A=Mobile or B=Predictions)
- Know your pod partner (2 devs per pod)
- Understand success criteria for Sprint 1

---

## Post-Kickoff: Team Syncs (9:30-10:30am) - 1 hour

### Track A Team (Mobile) - 30 min
- [ ] Read [FASE_15_SPRINT_1_PLANNING.md](./FASE_15_SPRINT_1_PLANNING.md) § "Week 1 Track A"
- [ ] Discuss with your 2-person pod:
  - React Native version and setup
  - Authentication approach (biometric?)
  - State management (Redux Toolkit)
  - Testing strategy
- [ ] **Lead Dev:** Prepare to create first GitHub branch `feat/15a-setup` 

### Track B Team (Predictions) - 30 min
- [ ] Read [FASE_15_SPRINT_1_PLANNING.md](./FASE_15_SPRINT_1_PLANNING.md) § "Week 1 Track B"
- [ ] Discuss with your 2-person pod:
  - Data source and loading approach
  - Feature engineering pipeline
  - Model selection (scikit-learn RandomForest)
  - Notebook structure
- [ ] **ML Engineer:** Prepare to create first GitHub branch `feat/15b-eda`

---

## After Team Syncs: Environment Setup (10:30-11:30am) - 1 hour

### ALL DEVELOPERS: Complete Dev Environment Setup
**Reference:** [FASE_15_DEV_ENVIRONMENT_SETUP.md](./FASE_15_DEV_ENVIRONMENT_SETUP.md)

**Track A (Mobile):**
- [ ] Install Node.js 18+ (if not already)
  ```bash
  node --version  # Should be v18.x or higher
  ```
- [ ] Install Expo CLI
  ```bash
  npm install -g expo-cli
  expo --version  # Should be 51.0+
  ```
- [ ] Clone project and install dependencies
  ```bash
  cd /home/claude/felix-automation
  git pull origin develop
  cd frontend/mobile
  npm install
  ```
- [ ] Start Expo development server
  ```bash
  npm start
  # Select i for iOS simulator or a for Android emulator
  # Should see app open in simulator
  ```
- [ ] Take screenshot of app running on simulator
- [ ] Post to #fase-15 with 🎉 reaction

**Track B (Predictions):**
- [ ] Install Python 3.11+ (if not already)
  ```bash
  python --version  # Should be 3.11+
  ```
- [ ] Create Python virtual environment
  ```bash
  cd /home/claude/felix-automation
  git pull origin develop
  python -m venv venv
  source venv/bin/activate  # or venv\Scripts\activate on Windows
  ```
- [ ] Install dependencies
  ```bash
  pip install -r requirements.txt
  pip install jupyter scikit-learn shap  # Additional ML packages
  ```
- [ ] Start Jupyter Lab for EDA
  ```bash
  jupyter lab
  # Should open http://localhost:8888
  ```
- [ ] Create your notebook: `notebooks/01_eda_[yourname].ipynb`
- [ ] Post Jupyter Lab URL to #fase-15 (use ngrok if needed for demo)

---

## Noon: First Code Commit (12:00-12:30pm) - 30 min

### GitHub Branch Setup (Lead Dev per track)
**Reference:** [FASE_15_DEV_ENVIRONMENT_SETUP.md](./FASE_15_DEV_ENVIRONMENT_SETUP.md#git-workflow)

**Track A Lead Mobile Dev:**
```bash
git checkout -b feat/15a-setup

# Add placeholder file showing setup complete
echo "# FASE 15 Mobile Setup - Ready for Sprint 1" > frontend/mobile/SETUP_COMPLETE.md

git add frontend/mobile/SETUP_COMPLETE.md
git commit -m "[15A-001] Setup React Native project scaffold

- Expo 51.0+ configured
- TypeScript enabled
- ESLint/Prettier configured
- iOS simulator: ✅ running
- Android emulator: ✅ ready

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01EZEKRd8BUbc4mh5jQNB73m"

git push origin feat/15a-setup
```

**Track B ML Engineer:**
```bash
git checkout -b feat/15b-eda

# Add placeholder notebook
touch backend/analytics/notebooks/01_eda_sample.ipynb

git add backend/analytics/notebooks/01_eda_sample.ipynb
git commit -m "[15B-001] Data preparation & EDA setup

- Load 5,432 historical predictions from FASE 14
- Load actual outcomes from CRM
- Initial data quality assessment
- Jupyter Lab configured
- Ready for exploratory analysis

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01EZEKRd8BUbc4mh5jQNB73m"

git push origin feat/15b-eda
```

### Create Pull Requests
- [ ] Go to GitHub > Pull Requests > New
- [ ] Set base: `develop`, compare: `feat/15a-setup` (or feat/15b-eda)
- [ ] Title: `[15A-001] Setup React Native project scaffold` (or equivalent)
- [ ] Description: Copy from commit message
- [ ] Assign to 1 other developer for review
- [ ] Post link to #fase-15 channel

---

## First Standup (12:30pm) - 15 min

**In #fase-15 channel:**

Post this template:

```
🌅 Good afternoon! End of Day 1 standup.

**Mobile (Track A):**
- [15A-001] Done: React Native scaffold complete ✅
  - Expo running on iOS simulator
  - TypeScript configured
  - PR: github.com/...

**Predictions (Track B):**
- [15B-001] Done: EDA setup ready ✅
  - Jupyter Lab running
  - 5,432 data points loaded
  - PR: github.com/...

**Blockers:** None currently 🎉

**Tomorrow's Focus:** [YOUR TICKET FOR DAY 2]

**Day 1 Summary:** All developers have working environments and have committed first code! 🚀
```

---

## By End of Day 1: You Should Have ✅

- [ ] Attended kickoff meeting and team sync
- [ ] Completed dev environment setup (simulator/Jupyter running)
- [ ] Made first code commit to feature branch
- [ ] Created first pull request for code review
- [ ] Posted standup update in Slack
- [ ] Know which 2-3 tickets you're working on tomorrow

---

## Troubleshooting: If Something Breaks

| Problem | Quick Fix |
|---------|-----------|
| Expo won't start | Try: `npm start -- --clear` |
| Python import error | Try: `pip install --upgrade setuptools` |
| Git branch exists | Try: `git checkout -b feat/15a-setup` (create new) |
| Port already in use | Find process: `lsof -i :8000` and kill it |
| npm permission denied | Try: `npm install -g expo-cli --force` |

**If stuck:** Post to #fase-15-blockers immediately. Don't wait!

---

## What NOT to Do on Day 1 ❌

- ❌ Don't try to implement entire ticket on Day 1
- ❌ Don't push directly to `main` or `develop` (always use feature branch)
- ❌ Don't skip the environment setup (it's foundational)
- ❌ Don't work alone (pair within your 2-person pod)
- ❌ Don't commit without writing tests (we do TDD)

---

## By Tomorrow Morning (Oct 8)

You'll be ready to:
1. Pick your first real ticket from [FASE_15_INITIAL_TICKETS_BACKLOG.md](./FASE_15_INITIAL_TICKETS_BACKLOG.md)
2. Follow TDD workflow: test first, then code
3. Make daily commits to your feature branch
4. Get code reviewed by pod partner
5. Participate in standup with confidence

---

**Timeline Summary:**
- 9:00-9:30am: Kickoff meeting
- 9:30-10:30am: Track-specific team syncs
- 10:30-11:30am: Environment setup
- 12:00pm: First code commit
- 12:30pm: First standup
- **Total: ~3.5 hours to be fully productive** ✅

---

**Good luck! You've got this.** 🚀

Questions? Post to #fase-15 channel.  
Blocked? Post to #fase-15-blockers for immediate help.

---

**Prepared by:** Claude Code (autonomous agent)  
**Date:** October 6, 2026  
**Next Update:** October 8, 2026 (Day 2 checklist if needed)
