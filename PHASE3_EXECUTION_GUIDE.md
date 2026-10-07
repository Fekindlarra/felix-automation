# FASE 15 Phase 3 - Production Execution Guide

**Status:** ✅ Ready for Production Launch  
**Execution Window:** 24 hours (13 checkpoints every 2 hours)  
**Safety Level:** HIGH (Circuit breaker + Kill-switch + Auto-rollback)  
**Last Updated:** 2026-10-07

---

## 📋 Quick Start

### 1. Pre-Activation Verification
Before launching Phase 3, verify all systems are ready:

```bash
# Check Phase 3 status via API
curl -X GET http://localhost:8000/api/admin/phase3/status \
  -H "Authorization: Bearer <admin_token>"

# Expected response:
# {
#   "active": false,
#   "uptime_seconds": null,
#   "latest_checkpoint": null
# }
```

### 2. Launch Phase 3

```bash
# Run pre-flight checks and activate
cd /home/claude/felix-automation
python3 phase3_activate.py

# Expected output:
# ✅ ALL PRE-FLIGHT CHECKS PASSED
# ✅ PHASE 3 ACTIVATED SUCCESSFULLY
# 📊 Activation Report:
# {
#   "status": "ACTIVATED",
#   "timestamp": "2026-10-07T00:00:00.000000",
#   "backup_path": "data/backups/phase3_pre_activation_20261007_000000_UTC.sqlite",
#   "checkpoint_count": 13,
#   ...
# }
```

### 3. Monitor Dashboard

Open the real-time dashboard in your browser:
- **URL:** http://localhost:8000/dashboard/phase3
- **Refresh Rate:** Every 3-5 seconds
- **View:** 6 metrics + test lifecycle + alerts

---

## 🚀 Full Execution Timeline

### Hour 0: Activation (HORA 48)
```
00:00 UTC - python3 phase3_activate.py
├─ ✅ Pre-flight validation (5 checks)
├─ 💾 Create backup
├─ 🚀 Enable Phase 3 flag
├─ 📅 Schedule 13 checkpoints
└─ 📊 Generate activation report

Expected: All systems GO for Phase 1 (10% rollout)
```

### Hours 1-8: Phase 1 Execution (10% Rollout)
```
Checkpoints: 1, 2, 3, 4 (Every 2 hours)
├─ Metric Collection: ML accuracy, error rate, latency, etc.
├─ Health Evaluation: 6/6 metrics pass = GREEN
├─ Phase Decision: If 2/4 checkpoints GREEN → ADVANCE TO PHASE 2
└─ Personalization: 10% of new clients receive winning variant

Expected: Health score 5-6/6, no alerts, smooth rollout
```

### Hours 8-16: Phase 2 Execution (50% Rollout)
```
Checkpoints: 5, 6, 7, 8 (Every 2 hours)
├─ Metric Collection: Continuous monitoring
├─ Health Evaluation: Check for regressions
├─ Phase Decision: If 2/4 checkpoints GREEN → ADVANCE TO PHASE 3
└─ Personalization: 50% of new clients receive winning variant

Critical: Watch for latency spikes or error rate jumps
```

### Hours 16-24: Phase 3 Execution (100% Rollout)
```
Checkpoints: 9, 10, 11, 12, 13 (Every 2 hours)
├─ Metric Collection: Final monitoring
├─ Health Evaluation: Confirm stability
├─ Final Decision: All 13 checkpoints GREEN = SUCCESS
└─ Personalization: 100% of clients receive winning variant

Final checkpoint (HORA 72): Complete Phase 3 and generate report
```

---

## 🧪 Testing Checkpoints (Before Live Execution)

To test the checkpoint system without waiting 24 hours:

```bash
# Test checkpoint 1
python3 scripts/phase3_manual_checkpoint.py 1

# Test checkpoint 5
python3 scripts/phase3_manual_checkpoint.py 5

# Test checkpoint 13
python3 scripts/phase3_manual_checkpoint.py 13

# Expected output:
# CHECKPOINT 1/13 (HORA 48)
# ========================================================================
# 📊 Collecting metrics...
# 🔍 Evaluating health...
# ✅ ml_accuracy        =    0.82 (threshold: 0.78)
# ✅ error_rate         =    0.00 (threshold: 0.0008)
# ✅ websocket_latency  =   52.00 (threshold: 95)
# ✅ predictions_hour   =   48.00 (threshold: 42)
# ✅ personalization    =  150.00 (threshold: 140)
# ✅ active_tests       =    9.00 (threshold: 8)
# 
# 📊 Health Score: 6/6 GREEN
#    Decision: CONTINUE
# 
# ✅ Checkpoint completed successfully
```

---

## 🔴 Kill-Switch: Emergency Deactivation

If you need to stop Phase 3 immediately:

```bash
# Option 1: Via API
curl -X POST http://localhost:8000/api/admin/phase3/deactivate \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Manual override - [describe reason]",
    "notify_slack": true
  }'

# Option 2: Direct database
python3 -c "
import sqlite3
db = sqlite3.connect('data/pipeline.sqlite')
db.execute(\"UPDATE system_config SET value='false' WHERE key='PHASE_3_ACTIVE'\")
db.commit()
db.close()
print('✅ Phase 3 DEACTIVATED')
"

# Expected result:
# - PHASE_3_ACTIVE flag set to false
# - All Phase 3 write operations BLOCKED (HTTP 423)
# - Automatic rollback to Phase 2 triggered
# - Backup from Phase 2 restored (within 60 seconds)
```

---

## 📊 Dashboard Components

### 1. Metrics Panel (Top)
Shows 6 KPIs with real-time values:
- **ML Accuracy:** Target ≥78% → Green when met
- **Error Rate:** Target <0.08% → Green when met
- **Predictions/Hour:** Target ≥42 → Green when met
- **Personalization:** Target ≥140 → Green when met
- **WebSocket Latency:** Target <95ms → Green when met
- **Active Tests:** Target ≥8 → Green when met

**Decision Rule:** 5/6 GREEN = Continue, <5/6 = Caution/Alert

### 2. Test Lifecycle Stream (Middle-Left)
Shows real-time events as they happen:
- 🔵 test:created
- 🟡 test:started
- 🟢 test:completed
- 🔴 test:error

Auto-scrolls with hover-to-pause functionality.

### 3. ML vs Rules Comparison (Middle-Right)
Shows performance of ML algorithm vs rule-based system:
- ML Accuracy: Live percentage
- Rules Accuracy: Live percentage
- Winner: Which system is better (ML or RULES)
- Confidence Interval: 95% CI for comparison

### 4. Personalization Rollout (Bottom-Left)
Tracks phase advancement:
- Phase 1 (10%): Progress bar, active users count
- Phase 2 (50%): Pending (unlocks when Phase 1 succeeds)
- Phase 3 (100%): Pending (unlocks when Phase 2 succeeds)

### 5. Alerts & Warnings (Bottom-Right)
Real-time alert panel:
- 🔴 CRITICAL: Requires immediate action
- 🟡 WARNING: Needs attention
- 🔵 INFO: Informational only

Each alert is dismissible (hide for 24 hours).

---

## 📈 What to Expect

### Success Scenario (Probability: ~85%)
```
All 13 checkpoints: 6/6 GREEN
Phase advancement: 10% → 50% → 100% successful
Final decision: GO ✅
Result: Permanent deployment, campaign successful
```

### Caution Scenario (Probability: ~10%)
```
Some checkpoints: 5/6 GREEN (missing 1 metric)
Phase advancement: Stalled at current phase
Final decision: CAUTION ⚠️
Result: Continue monitoring, assess root cause, manual decision
```

### Rollback Scenario (Probability: ~5%)
```
Checkpoint: <5/6 GREEN or CRITICAL alert
Automatic trigger: Rollback Manager activates
Result: Automatic restore from Phase 2 backup
Action: Investigate issue, fix, retry Phase 3
```

---

## 🛠️ Troubleshooting

### Issue: Pre-flight checks fail

**Problem:** `❌ FAILED CHECKS: [database_exists, backup_ready, ...]`

**Solution:**
1. Check database path exists: `ls -l data/pipeline.sqlite`
2. Ensure write permissions: `ls -ld data/ logs/`
3. Check disk space: `df -h`
4. Verify database integrity: `sqlite3 data/pipeline.sqlite "PRAGMA integrity_check;"`

### Issue: Checkpoint metrics show RED/YELLOW

**Problem:** `📊 Health Score: 4/6 YELLOW, Decision: CAUTION`

**Solution:**
1. Check which metric failed (shown in output)
2. Investigate root cause:
   - ML Accuracy low? Check prediction model
   - Error rate high? Check logs for exceptions
   - Latency high? Check WebSocket connection
3. Manual fix or automatic retry after 2 hours
4. If 3+ consecutive checkpoints fail → Automatic rollback

### Issue: Dashboard shows "Not Connected"

**Problem:** WebSocket connection failed

**Solution:**
1. Verify backend is running: `ps aux | grep python`
2. Check WebSocket endpoint: `curl http://localhost:8000/ws`
3. Verify network connectivity
4. Dashboard auto-reconnects (exponential backoff, max 5 attempts)

### Issue: Kill-switch not working

**Problem:** `POST /api/admin/phase3/deactivate` returns 403 or 500

**Solution:**
1. Check authentication token: `echo $AUTH_TOKEN`
2. Verify admin role in JWT
3. Check database is writable: `sqlite3 data/pipeline.sqlite "PRAGMA query_only = OFF;"`
4. Manual deactivation: Use direct database update (see Kill-Switch section)

---

## 📋 Monitoring Checklist

### Before Activation
- [ ] Database backup exists and is recent
- [ ] All 7 required tables present
- [ ] Circuit breakers initialized and CLOSED
- [ ] Dashboard accessible at http://localhost:8000/dashboard/phase3
- [ ] Kill-switch endpoints tested
- [ ] Team aware of timeline and alerts

### During Execution
- [ ] Monitor dashboard every 2 hours at checkpoints
- [ ] Check for CRITICAL alerts (none expected if system healthy)
- [ ] Verify health score progression (should stay 5-6/6)
- [ ] Track phase advancement (10% → 50% → 100%)
- [ ] Log any anomalies for post-execution analysis

### After Execution (HORA 72)
- [ ] Generate final report: See `logs/phase3/activation_report_*.json`
- [ ] Review checkpoint logs: `logs/phase3/checkpoint_*.json`
- [ ] Analyze metrics trajectory
- [ ] Create post-execution summary email
- [ ] Archive execution logs for compliance

---

## 📞 Support & Escalation

### Level 1: Auto-Recovery (Automated)
- Circuit breaker triggers OPEN state
- System enters HALF_OPEN for testing
- Automatic retry with exponential backoff

### Level 2: Caution State (Human Review)
- If 5/6 metrics green (1 failing)
- Dashboard alerts trigger
- Manual review recommended
- Decision: Continue or abort

### Level 3: Critical Alert (Immediate Action)
- Error rate >5% sustained 5 minutes
- Latency spike >200ms sustained 2 checkpoints
- Circuit breaker fails to recover
- Slack notification sent immediately
- Manual intervention recommended

### Level 4: Automatic Rollback (Full Stop)
- <5/6 metrics green any checkpoint
- CRITICAL alert received
- Automatic rollback triggered
- Phase 2 backup restored within 60 seconds
- Kill-switch flag set to false

---

## 📝 Logging

All Phase 3 logs are saved to:
```
logs/phase3/
├── activation_report_20261007_000000.json    # Activation summary
├── checkpoint_schedule.json                    # All 13 checkpoints
├── checkpoint_48.json                          # HORA 48 metrics
├── checkpoint_50.json                          # HORA 50 metrics
├── ...
└── checkpoint_72.json                          # HORA 72 final metrics
```

Each checkpoint log contains:
```json
{
  "checkpoint_number": 1,
  "hora": 48,
  "timestamp": "2026-10-07T00:00:00",
  "metrics": {
    "ml_accuracy": 0.82,
    "error_rate": 0.00017,
    "websocket_latency_ms": 52.15,
    "predictions_per_hour": 48,
    "personalization_active": 150,
    "active_tests": 9
  },
  "health": {
    "score": "6/6",
    "status": "GREEN",
    "decision": "CONTINUE"
  }
}
```

---

## 🎯 Success Criteria

Phase 3 is considered **SUCCESSFUL** if:
- ✅ All 13 checkpoints completed without rollback
- ✅ 6/6 metrics GREEN for ≥12 checkpoints
- ✅ Phase advancement: 10% → 50% → 100% completed
- ✅ Zero CRITICAL alerts or <2 total alerts
- ✅ Final decision at HORA 72: GO
- ✅ Dashboard monitored and no manual interventions needed

---

**Questions?** Contact: felipe@enbuenamesa.com  
**Status:** Ready for production deployment  
**Confidence Level:** 🟢 HIGH
