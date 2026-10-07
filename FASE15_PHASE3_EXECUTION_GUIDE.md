# FASE 15 Phase 3 - Production Execution Guide

**Last Updated:** October 6, 2026  
**Status:** PRODUCTION READY ✅  
**Duration:** 24-hour execution window (HORA 48-72)

---

## 📋 Executive Summary

Phase 3 is a 24-hour production test (HORA 48-72) that validates ML-based personalization at scale:
- **Goal:** Verify 6/6 health metrics remain GREEN throughout 24-hour window
- **Success Criteria:** 5 out of 6 metrics healthy at each checkpoint
- **Risk Mitigation:** Automatic rollback if metrics degrade
- **Kill-Switch:** Manual emergency deactivation available via API

---

## 🚀 Pre-Execution Checklist

### 1. System Readiness Verification
```bash
# Run preflight validation (must pass all 5 checks)
python3 /home/claude/felix-automation/backend/phase3_preflights.py

# Verify infrastructure components
python3 /home/claude/felix-automation/verify_phase3_infrastructure.sh
```

**5 Required Pre-Flight Checks:**
- ✅ Phase 2 Error Rate < 1% (from last 24h metrics)
- ✅ Recent Database Backups (< 2 hours old)
- ✅ Database Integrity (all tables present)
- ✅ System Components Healthy (DB, WebSocket, monitoring)
- ✅ Circuit Breakers Functional (no OPEN breakers)

### 2. Database Backup Verification
```bash
# Verify recent backups exist
ls -lh data/backups/ | grep -E "\.sqlite|\.db"

# Backup requirements
# - At least one backup within last 2 hours
# - Database size > 1MB (indicates data present)
```

### 3. Monitoring Infrastructure
```bash
# Verify monitoring daemon will start
python3 -c "from backend.monitoring_daemon import MonitoringDaemon; m=MonitoringDaemon(); print('✅ Monitoring daemon importable')"

# Verify WebSocket manager
python3 -c "from routers.websocket import ConnectionManager; c=ConnectionManager(); print('✅ WebSocket manager ready')"
```

### 4. Admin Dashboard Ready
- ✅ Access `/frontend/phase3_realtime_dashboard.html`
- ✅ Verify WebSocket connection status indicator
- ✅ Test export metrics functionality
- ✅ Test emergency stop button

---

## ⚡ Activation Process

### Step 1: Run Pre-Flight Checks (One-time)
```bash
cd /home/claude/felix-automation
python3 phase3_activate.py
```

**Expected Output:**
```
✅ All pre-flight checks PASSED!
💾 Creating database backup at: data/backups/phase3_start_20261006_223456.sqlite
⚡ Activating Phase 3...
✅ Phase 3 activated in database

📊 ACTIVATION SUMMARY:
- Activation Timestamp: 2026-10-06T22:34:56.000000+00:00
- Backup Location: data/backups/phase3_start_20261006_223456.sqlite
- Status: ACTIVE - Beginning 24-hour test
- First Checkpoint: HORA 50 (in ~2 hours)
```

**If Pre-Flight Checks FAIL:**
- Address blocked reason (e.g., "backup_recent" or "phase2_health")
- Rerun checks after fixing issue
- Do NOT proceed with activation

### Step 2: Activate via API (Alternative Method)
```bash
# Admin token required
ADMIN_TOKEN="<your-24-hour-jwt-token>"

curl -X POST http://localhost:8000/api/admin/phase3/activate \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Manual activation - scheduled production test"}'
```

**Expected Response:**
```json
{
  "status": "activated",
  "timestamp": "2026-10-06T22:34:56.000000",
  "message": "Phase 3 activated. First checkpoint in ~2 hours. Backup: data/backups/phase3_start_20261006_223456.sqlite"
}
```

---

## 📊 Monitoring During Execution

### Real-Time Dashboard
**URL:** `http://localhost:8000/frontend/phase3_realtime_dashboard.html`

**Live Metrics Display:**
1. **ML Accuracy** (Target: ≥78%) - Real-time accuracy of ML model vs. rules
2. **Error Rate** (Target: <0.08%) - Percentage of failed predictions
3. **WebSocket Latency** (Target: <95ms) - Real-time communication delay
4. **Predictions/Hour** (Target: ≥42) - Throughput of ML service
5. **Personalization Active** (Target: ≥140) - Number of personalized clients
6. **Active Tests** (Target: ≥8) - Number of concurrent A/B tests

**Health Status Indicator:**
- 🟢 **6/6 GREEN:** All metrics healthy → CONTINUE
- 🟡 **5/6 GREEN:** One metric marginal → CAUTION (continue monitoring)
- 🔴 **<5/6 GREEN:** Two+ metrics unhealthy → PREPARE ROLLBACK

### Checkpoint Monitoring

**Automatic checkpoints occur every 2 hours:**
- **HORA 50:** 2 hours after activation
- **HORA 52, 54, 56...** (every 2 hours)
- **HORA 72:** Final checkpoint (24-hour mark)

**Each checkpoint generates:**
1. Health metrics snapshot
2. Decision: CONTINUE/CAUTION/ROLLBACK
3. Phase advancement check (if metrics allow)
4. JSON report saved: `logs/phase3/checkpoint_HORA_XX.json`

**Example Checkpoint Report:**
```json
{
  "hora": 50,
  "timestamp": "2026-10-06T22:50:00Z",
  "metrics": {
    "ml_accuracy": 0.835,
    "error_rate": 0.0015,
    "websocket_latency": 8,
    "predictions_hour": 48,
    "personalization_active": 150,
    "active_tests": 9
  },
  "status": "6/6 GREEN",
  "decision": "CONTINUE",
  "alerts": []
}
```

### Event Stream Monitoring
Dashboard displays real-time events:
- 🔵 `test:created` - New A/B test launched
- 🟡 `test:started` - Test began collecting data
- 🟢 `test:completed` - Test finished
- 🎯 `test:winner_announced` - Winning variant identified
- 📊 `comparison:completed` - ML vs Rules comparison finalized

---

## 📈 Rollout Phases

Phase 3 uses gradual rollout to minimize risk:

### Phase 1: 10% Rollout (HORA 48-56)
- Personalized variant deployed to 10% of new clients
- Monitoring: Check for edge cases, performance issues
- Advancement Criteria: 2 consecutive healthy checkpoints

### Phase 2: 50% Rollout (HORA 56-64)
- If Phase 1 successful: Expand to 50% of new clients
- Monitoring: Watch for volume-related issues
- Advancement Criteria: 2 more consecutive healthy checkpoints

### Phase 3: 100% Rollout (HORA 64-72)
- If Phase 2 successful: Deploy to all new clients
- Monitoring: Final validation at scale
- Decision Point: HORA 72 (24-hour mark)

**Dashboard displays rollout progress:**
```
Phase 1: 10% Rollout  ███░░░░░░ 35%
Phase 2: 50% Rollout  ░░░░░░░░░░ 0%
Phase 3: 100% Rollout ░░░░░░░░░░ 0%
```

---

## 🚨 Automatic Rollback Conditions

Phase 3 automatically triggers rollback if:

1. **Error Rate Spike:** Sustained >5% error rate for 5+ minutes
2. **Latency Degradation:** WebSocket latency >200ms sustained 2+ checkpoints
3. **ML Accuracy Drop:** Accuracy <70% for any checkpoint
4. **Circuit Breaker Open:** Any critical service unavailable
5. **Health Score:** <5/6 metrics healthy at any checkpoint
6. **CRITICAL Alert:** System sends high-priority alert

**Automatic Response:**
1. Restore database from checkpoint backup
2. Revert personalization to Phase 2 rules
3. Divert traffic back to Phase 2 ML service
4. Alert monitoring team
5. Log detailed rollback reason
6. Stop Phase 3 checkpoint monitoring

---

## 🛑 Emergency Stop Procedure

### Option 1: Dashboard Emergency Button
1. Open Phase 3 Real-Time Dashboard
2. Scroll to bottom → "⚙️ Controls" section
3. Click red "🛑 Emergency Stop" button
4. Confirm deactivation in popup

### Option 2: API Emergency Deactivation
```bash
ADMIN_TOKEN="<your-24-hour-jwt-token>"

curl -X POST http://localhost:8000/api/admin/phase3/deactivate \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Emergency stop - critical metric violation"}'
```

**Expected Response:**
```json
{
  "status": "deactivated",
  "timestamp": "2026-10-06T22:50:00.000000",
  "message": "Phase 3 deactivated. Rollback in progress. Traffic reverted to Phase 2."
}
```

### Option 3: Database Manual Override
```sql
-- Connect to database
sqlite3 fase15.db

-- Immediately disable Phase 3
UPDATE system_config SET value='false' WHERE key='PHASE_3_ACTIVE';
COMMIT;

-- Verify
SELECT value FROM system_config WHERE key='PHASE_3_ACTIVE';
```

---

## 📊 Metrics Interpretation Guide

### ML Accuracy (Target: ≥78%)
- **What:** Percentage of personalization decisions that were optimal
- **Why:** Shows ML model is making better decisions than rules
- **Healthy Range:** 78-95%
- **Action if Low:** Review model training data, recheck feature engineering

### Error Rate (Target: <0.08%)
- **What:** Percentage of API calls that returned errors
- **Why:** System reliability indicator
- **Healthy Range:** 0.01-0.08%
- **Action if High:** Check database logs, review circuit breaker status

### WebSocket Latency (Target: <95ms)
- **What:** Time for real-time dashboard updates to reach browser
- **Why:** User experience indicator
- **Healthy Range:** 8-30ms normal, <95ms acceptable
- **Action if High:** Check network, review broadcasting performance

### Predictions/Hour (Target: ≥42)
- **What:** Number of personalization decisions made
- **Why:** System throughput indicator
- **Healthy Range:** 42-100+ per hour
- **Action if Low:** Check prediction service health, review database connections

### Personalization Active (Target: ≥140)
- **What:** Number of clients receiving personalized content
- **Why:** Rollout progress indicator
- **Healthy Range:** 140-300+ (depends on user base)
- **Action if Low:** Check personalization engine, review rollout phase

### Active Tests (Target: ≥8)
- **What:** Number of concurrent A/B tests
- **Why:** Experimentation health indicator
- **Healthy Range:** 8-20+ concurrent tests
- **Action if Low:** Check test creation, review test completion rates

---

## 📝 Post-Execution Analysis

### After HORA 72 (24-hour mark)

#### 1. Generate Final Report
```bash
python3 /home/claude/felix-automation/phase3_generate_report.py
```

**Output:**
- `reports/phase3_final_report.md` - Human-readable summary
- `reports/phase3_final_report.json` - Machine-readable data
- `reports/phase3_final_report.html` - Interactive visualization

#### 2. Create Executive Summary Email
```bash
# Email sent to felipe@enbuenamesa.com with:
# - 1-sentence status (SUCCESS/CAUTION/NO-GO)
# - 3 key metrics
# - Checkpoint summary table
# - Business impact calculation
# - Recommendations

python3 /home/claude/felix-automation/phase3_send_summary_email.py
```

#### 3. Analysis Dashboard
**URL:** `http://localhost:8000/frontend/phase3_analysis_dashboard.html`

Features:
- Timeline view of all 6 metrics across 13 checkpoints
- Trend analysis (improving/degrading)
- Comparative view: Phase 2 vs Phase 3 side-by-side
- Alert timeline: when each alert fired + resolution
- Decision log: every go/caution/no-go decision

#### 4. Success Criteria Evaluation

**Minimum Success (5/6 metrics):**
- ✅ ML Accuracy ≥78%
- ✅ Error Rate <0.08%
- ✅ WebSocket Latency <95ms
- ✅ Predictions/Hour ≥42
- ✅ Personalization ≥140
- ⚠️  Active Tests ≥8 (optional)

**Expected Outcome (6/6 metrics):**
- ✅ All 6 metrics GREEN throughout 24-hour window
- ✅ Phase advancement: 10% → 50% → 100% successful
- ✅ No rollbacks triggered
- ✅ Zero CRITICAL alerts
- ✅ Dashboard updated every 5 seconds (no lag)

---

## 🔧 Troubleshooting Guide

### Issue: Pre-Flight Checks Fail
**Solution:**
1. Check specific blocked reason in activation output
2. If `phase2_health`: Wait for Phase 2 error rate to normalize
3. If `backup_recent`: Manually create backup: `cp fase15.db data/backups/phase3_manual_$(date +%s).sqlite`
4. If `database_integrity`: Run `backend/init_database.py` to create missing tables
5. If `components_healthy`: Verify monitoring daemon started
6. If `circuit_breakers_ok`: Check circuit breaker registry, reset if needed

### Issue: WebSocket Not Connecting
**Dashboard shows:** "Disconnected - Reconnecting..."

**Solution:**
1. Verify WebSocket server running: `netstat -tlnp | grep 8000`
2. Check if proxy/firewall blocking WS: Test in browser console
3. Verify `ws://localhost:8000/ws` is accessible
4. Check browser console for specific WebSocket error
5. Restart FastAPI application

### Issue: Metrics Not Updating
**Dashboard shows:** "--" for all metrics

**Solution:**
1. Verify monitoring daemon thread is running
2. Check `logs/monitoring.log` for errors
3. Verify database `system_config` table has metrics being written
4. Query: `SELECT * FROM system_config WHERE key LIKE '%metric%';`
5. If empty, check that monitoring components are recording data

### Issue: Checkpoint Not Triggered
**Expected:** Checkpoint every 2 hours, none appear after 2+ hours

**Solution:**
1. Verify Phase 3 flag is set: `SELECT value FROM system_config WHERE key='PHASE_3_ACTIVE';`
2. Check monitoring daemon logs for phase3_checkpoint_loop errors
3. Manually trigger checkpoint: `python3 scripts/phase3_manual_checkpoint.py`
4. Review checkpoint threshold: Should be 2 hours (7200 seconds)

### Issue: Automatic Rollback Triggered
**Dashboard shows:** "Phase 3 DEACTIVATED" with rollback reason

**Solution:**
1. Read rollback reason in dashboard alert
2. Check logs: `tail -100 logs/monitoring.log | grep -i rollback`
3. Review specific metric that failed (see logs)
4. Fix underlying issue (e.g., database query optimization if latency spike)
5. Optional: Wait and re-activate once issue resolved

### Issue: Emergency Stop Button Not Working
**Button click does nothing:**

**Solution:**
1. Verify admin token in browser localStorage
2. Check browser console for fetch errors
3. Manually deactivate via API (see Emergency Stop Procedure)
4. Verify admin role: POST endpoint requires `role="admin"`
5. Create new admin token if expired

---

## 📁 File Structure Reference

```
/home/claude/felix-automation/
├── phase3_activate.py              # Activation script (run first!)
├── backend/
│   ├── routes/
│   │   ├── phase3_admin_routes.py  # Kill-switch endpoints (/api/admin/phase3/*)
│   │   └── ab_testing_routes.py    # A/B testing with Phase 3 guards
│   ├── phase3_preflights.py        # 5 pre-flight validation checks
│   ├── monitoring_daemon.py        # Background monitoring (includes checkpoint loop)
│   ├── rollback_manager.py         # Automatic rollback decision logic
│   ├── circuit_breaker.py          # Circuit breaker pattern
│   └── api/main.py                 # FastAPI app initialization
├── agents/
│   ├── personalization_engine.py   # Rollout phase management
│   └── ml_vs_rules_comparator.py   # ML accuracy comparison
├── frontend/
│   ├── phase3_realtime_dashboard.html      # Real-time 6-metric dashboard
│   ├── phase3_analysis_dashboard.html      # Post-execution analysis
│   └── ab_testing_dashboard.html           # Main dashboard (backup)
├── logs/
│   └── phase3/
│       ├── checkpoint_HORA_50.json         # Generated during execution
│       ├── checkpoint_HORA_52.json
│       └── checkpoint_HORA_72.json
├── reports/
│   ├── phase3_final_report.md              # Generated after HORA 72
│   ├── phase3_final_report.json
│   └── phase3_final_report.html
└── data/
    └── backups/
        └── phase3_start_20261006_223456.sqlite  # Backup from activation
```

---

## 🎯 Key Decisions & Rationale

### Why 2-Hour Checkpoints?
- **13 checkpoints** over 24 hours = 2-hour intervals
- Balances monitoring frequency with data collection time
- Allows time for metrics to stabilize after phase changes

### Why 5/6 Metrics for GO Decision?
- **Robustness:** One metric can temporarily spike without full rollback
- **Confidence:** 5/6 (83%) confidence level acceptable for production
- **Reality:** Perfect metrics rare; 5/6 indicates healthy operation

### Why Gradual Rollout (10% → 50% → 100%)?
- **Risk Management:** Catch issues early with small user base
- **Validation:** Each phase proves concept at next scale level
- **Reversibility:** Can pause/revert at each phase if needed

### Why Circuit Breaker Pattern?
- **Fault Isolation:** Failures in one service don't cascade
- **Auto-Recovery:** System attempts recovery after timeout
- **Observability:** Clear signal of service degradation

---

## 📞 Escalation Path

**If Phase 3 fails or needs immediate help:**

1. **First 30 seconds:** Hit Emergency Stop button (dashboard or API)
2. **Next 2 minutes:** Verify database rollback completed
3. **Next 5 minutes:** Check phase3_realtime_dashboard.html for status
4. **Next 15 minutes:** Review `phase3_generate_report.py` output
5. **Escalation:** Contact Felipe (felipe@enbuenamesa.com) with:
   - Rollback reason (if auto-triggered)
   - Checkpoint hour when failure detected
   - Metrics snapshot from dashboard

---

## ✅ Deployment Checklist

Before activation, verify:

- [ ] All 5 pre-flight checks pass
- [ ] Database backups present and recent
- [ ] Monitoring daemon tested and working
- [ ] WebSocket connection verified in browser
- [ ] Emergency stop button tested
- [ ] Admin token generated and valid (24-hour expiry)
- [ ] Phase 3 dashboard loads without errors
- [ ] All 6 metrics display in dashboard
- [ ] Event log streaming works
- [ ] Export metrics button functional
- [ ] Team members can access live dashboard
- [ ] Rollback procedure documented and tested
- [ ] Communication plan in place (Slack/email alerts)

---

**Status:** ✅ PRODUCTION READY  
**Last Tested:** October 6, 2026  
**Next Review:** Post-execution analysis (after HORA 72)

---

## Quick Reference: Commands

```bash
# 1. Activate Phase 3
python3 phase3_activate.py

# 2. View real-time dashboard
open http://localhost:8000/frontend/phase3_realtime_dashboard.html

# 3. Check status via API
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/phase3/status

# 4. Emergency deactivation
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/phase3/deactivate \
  -d '{"reason":"Emergency"}'

# 5. Generate final report (after HORA 72)
python3 phase3_generate_report.py

# 6. Send executive summary
python3 phase3_send_summary_email.py
```

---
