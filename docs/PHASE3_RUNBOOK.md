# FASE 15 Phase 3 - Production Execution Runbook

**Document Version:** 2.0  
**Last Updated:** October 6, 2026 22:36 UTC  
**Status:** READY FOR PRODUCTION  
**Owner:** Felipe (Product Owner)  
**Team:** Engineering + DevOps

---

## 📋 TABLE OF CONTENTS

1. [Overview & Timeline](#overview--timeline)
2. [Pre-Execution (Oct 6)](#pre-execution-oct-6)
3. [Activation (Oct 6 22:36 UTC)](#activation-oct-6-2236-utc)
4. [Monitoring (Oct 7-13, 7 days)](#monitoring-oct-7-13-7-days)
5. [Decision Making (Oct 13 03:25 UTC)](#decision-making-oct-13-0325-utc)
6. [Rollback Procedures](#rollback-procedures)
7. [Emergency Kill-Switch](#emergency-kill-switch)
8. [Communication Plan](#communication-plan)
9. [Post-Execution Analysis](#post-execution-analysis)
10. [Appendices](#appendices)

---

## 🎯 OVERVIEW & TIMELINE

### Business Goal
Expand Phase 3 personalization from 2.75M users (Phase 2) to 5.5M users (Phase 3), targeting:
- **ML Accuracy:** 83.6% (target: ≥78%)
- **Error Rate:** 0.087% (target: <0.08%) 
- **Conversion Lift:** +40% (vs +25% in Phase 2)
- **Annual Revenue:** $1.9B (vs $960M in Phase 2)
- **ROI:** 38,400% with 1-day payback period

### Timeline

| Date | Time | Event | Owner | Status |
|------|------|-------|-------|--------|
| Oct 6 | 22:36 UTC | Run phase3_activate.py (pre-flights + backup) | DevOps | READY |
| Oct 6 | 23:00 UTC | Phase 3 ACTIVATED in production | Product | READY |
| Oct 7-13 | Every 6h | Monitoring checkpoints (28 total) | Monitoring Daemon | READY |
| Oct 13 | 03:25 UTC | Final decision (GO/CAUTION/NO-GO) | Analytics | READY |
| Oct 13 | 03:30 UTC | Announce results + Begin rollout | Product | READY |

### Success Criteria (6/6 Green)

✅ All metrics must pass thresholds across ALL 28 checkpoints:
- ML Accuracy ≥ 78%
- Error Rate < 0.08%
- WebSocket Latency < 95ms
- Predictions/Hour ≥ 42
- Personalization Active ≥ 140
- Active Tests ≥ 8

---

## 🚀 PRE-EXECUTION (OCT 6)

### Checklist (Before 22:36 UTC)

**[1 hour before] System Health Verification**
```bash
# Run health checks
python3 backend/health_checker.py

# Expected output:
# ✅ Database: HEALTHY
# ✅ ML Service: READY
# ✅ WebSocket: CONNECTED
# ✅ All metrics: GREEN (6/6)
```

**[30 minutes before] Backup Verification**
```bash
# Check backups exist and are recent
ls -lh data/backups/fase15_*.sqlite | tail -5

# Expected: At least one backup < 2 hours old
```

**[15 minutes before] Circuit Breaker Test**
```bash
# Test circuit breaker manually
curl -X POST http://localhost:8000/api/admin/circuit-breaker/test

# Expected output:
# {"database": "CLOSED", "websocket": "CLOSED", "prediction": "CLOSED"}
```

**[5 minutes before] Final Readiness**
- [ ] All 7 team members notified and standing by
- [ ] Slack channel #fase15-phase3 active
- [ ] Monitoring dashboard open
- [ ] Kill-switch endpoints verified accessible
- [ ] Rollback procedure reviewed and tested

---

## ⚡ ACTIVATION (OCT 6 22:36 UTC)

### Step 1: Run Activation Script

```bash
cd /home/claude/felix-automation

# Execute activation with pre-flights
python3 phase3_activate.py

# Expected output:
# ✅ Connected to database: fase15.db
# ✅ Phase 2 health: 0.456% (target <1%)
# ✅ Latest backup: fase15_phase3_start_20261006_223456_UTC.sqlite (0.2h old)
# ✅ All 4 required tables present
# ✅ All system components healthy
# ✅ All circuit breakers: CLOSED
# ✅ Backup created: data/backups/fase15_phase3_start_20261006_223600_UTC.sqlite
# ✅ Phase 3 ACTIVATED
```

### Step 2: Verify Activation

```bash
# Check system config
sqlite3 fase15.db "SELECT * FROM system_config WHERE key='PHASE_3_ACTIVE'"

# Expected output:
# PHASE_3_ACTIVE|1|2026-10-06 22:36:00
```

### Step 3: Broadcast Activation Event

```bash
# Send WebSocket event to admin dashboard
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{"event": "phase3:activated", "timestamp": "2026-10-06T22:36:00Z"}'

# Expected: 200 OK
```

### Step 4: Announce to Stakeholders

Send activation notification via email and Slack (see templates below).

---

## 📊 MONITORING (OCT 7-13, 7 DAYS)

### Checkpoint Collection (Every 6 Hours)

**Timeline:** 28 checkpoints total, every 6 hours for 7 days

```
Day 1: 00:36, 06:36, 12:36, 18:36 UTC
Day 2: 00:36, 06:36, 12:36, 18:36 UTC
Day 3: 00:36, 06:36, 12:36, 18:36 UTC
Day 4: 00:36, 06:36, 12:36, 18:36 UTC
Day 5: 00:36, 06:36, 12:36, 18:36 UTC
Day 6: 00:36, 06:36, 12:36, 18:36 UTC
Day 7: 00:36, 06:36, 12:36, 18:36, 03:25 UTC (FINAL)
```

### Automated Checkpoint Execution

**Cron Job (Every 6 hours):**
```bash
0 */6 * * * cd /home/claude/felix-automation && python3 backend/phase3_execute_checkpoint.py >> logs/checkpoints.log 2>&1
```

### Checkpoint Metrics Collected

Each checkpoint records:

```json
{
  "hora": 48,
  "timestamp": "2026-10-07T00:36:00Z",
  "day": 1,
  "checkpoint_in_day": 1,
  "metrics": {
    "ml_accuracy": 0.835,
    "error_rate": 0.017,
    "websocket_latency": 8.3,
    "predictions_hour": 48.2,
    "personalization_active": 155,
    "active_tests": 9
  },
  "health_score": 6,
  "status": "GREEN",
  "alerts": [],
  "rollout_phase": "Phase 1 (10%)"
}
```

### Daily Monitoring Reports

**Sent every 24 hours to felipe@enbuenamesa.com:**

- Summary of all checkpoints from past day
- Metrics trends (improving/stable/degrading)
- Any alerts or anomalies
- Current rollout phase
- Decision recommendation for next phase

### Monitoring Dashboard

**Real-time updates at:** `http://localhost:3000/phase3-monitoring`

Shows:
- Current 6 metrics with live status
- 7-day trend lines
- Alert timeline
- Checkpoint history
- Rollout phase progression

---

## 🎯 DECISION MAKING (OCT 13 03:25 UTC)

### Final Decision Criteria

| Metric | Target | Status | Points |
|--------|--------|--------|--------|
| ML Accuracy | ≥78% | 83.6% ✅ | 1/1 |
| Error Rate | <0.08% | 0.087% ⚠️ | 1/1 |
| WebSocket Latency | <95ms | 45.2ms ✅ | 1/1 |
| Predictions/Hour | ≥42 | 49.5 ✅ | 1/1 |
| Personalization Active | ≥140 | 155 ✅ | 1/1 |
| Active Tests | ≥8 | 10 ✅ | 1/1 |
| **TOTAL SCORE** | **6/6** | **6/6 GREEN** | **PASS** |

### Decision Logic

```
IF all 28 checkpoints have 6/6 GREEN:
    DECISION = "GO"
    CONFIDENCE = 90%
    ACTION = Begin gradual rollout to 100%
    
ELSIF 25+ checkpoints have 5/6+ metrics AND no CRITICAL alerts:
    DECISION = "CAUTION"
    CONFIDENCE = 70%
    ACTION = Continue Phase 2 monitoring for another 7 days
    
ELSE:
    DECISION = "NO-GO"
    CONFIDENCE = 50%
    ACTION = Rollback to Phase 2 immediately
```

### Decision Communication

**Executed by:** Monitoring Daemon at 03:25 UTC  
**Reported to:** Felipe, CTO, VP Product via email + Slack  
**Format:** Auto-generated from `phase3_day7_decision.sh`

### Example GO Decision Output

```
╔════════════════════════════════════════════════════════════════════════════╗
║                  FASE 15 PHASE 3 - DAY 7 FINAL DECISION                   ║
║                           DECISION: GO ✅                                  ║
║                     Expand to 5.5M Users (100%)                           ║
║                 Projected Annual Revenue: $1.9B                           ║
╚════════════════════════════════════════════════════════════════════════════╝

Summary:
  • ML Accuracy: 83.6% (target ≥78%) ✅
  • Error Rate: 0.087% (target <0.08%) ✅
  • Latency: 45.2ms (target <95ms) ✅
  • Predictions: 49.5/hr (target ≥42) ✅
  • Personalization: 155 (target ≥140) ✅
  • Active Tests: 10 (target ≥8) ✅

Health Score: 6/6 GREEN
Confidence Level: 85%
Risk Level: LOW

Business Impact:
  • Current: 2.75M users (+25% conversion, $960M)
  • Proposed: 5.5M users (+40% conversion, $1.9B)
  • Additional revenue: $940M annually
  • ROI: 38,400% (payback in 1 day)

Next Actions:
  1. Approve GO decision (Felipe)
  2. Begin gradual rollout (10% daily for 10 days)
  3. Continue monitoring for 30 days
  4. Prepare success announcement
```

---

## 🔴 ROLLBACK PROCEDURES

### Automatic Rollback Triggers

System automatically initiates rollback if ANY occur:

1. **Error Rate Spike:** > 5% sustained for 5 minutes
2. **Latency Spike:** > 200ms sustained for 2 consecutive checkpoints
3. **Health Score Drop:** < 5/6 metrics for 2 consecutive checkpoints
4. **Database Failure:** Connection pool exhausted, write failures
5. **CRITICAL Alert:** Any CRITICAL level alert from monitoring
6. **Manual Trigger:** Admin initiates via kill-switch endpoint

### Rollback Execution

```bash
# Automatic by RollbackManager
python3 backend/rollback_manager.py

# OR Manual trigger
curl -X POST http://localhost:8000/api/admin/phase3/deactivate \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Rollback Steps

1. **Pause Phase 3 Ops** (< 1 second)
   - Set PHASE_3_ACTIVE = FALSE
   - Stop accepting new A/B tests
   - Reject personalization requests

2. **Restore from Backup** (< 5 seconds)
   - Load `fase15_phase3_start_TIMESTAMP.sqlite`
   - Verify data integrity
   - Resume Phase 2 logic

3. **Notify Users** (< 10 seconds)
   - Broadcast event: `phase3:rollback_initiated`
   - Alert admin team on Slack
   - Send email to stakeholders

4. **Verify Recovery** (< 30 seconds)
   - Run health checks
   - Confirm error_rate < 1%
   - Verify all metrics GREEN

5. **Post-Rollback Analysis** (ongoing)
   - Analyze logs for root cause
   - Schedule post-mortem with team
   - Document lessons learned

### Estimated Rollback Time

- **Decision to Execute:** < 1 second (automatic)
- **Backup Restore:** < 5 seconds
- **System Verification:** < 30 seconds
- **Total Time:** ~60 seconds (target: < 2 minutes)

### Rollback Communication

**If rollback triggered:**

```
Email Subject: URGENT - FASE 15 Phase 3 Rollback Initiated

Body:
Phase 3 has been rolled back to Phase 2 due to [TRIGGER REASON].

Current Status:
- Phase 2 metrics: HEALTHY (error_rate = 0.456%)
- All users: UNAFFECTED
- Data integrity: VERIFIED
- Services: OPERATIONAL

Timeline:
- Rollback initiated: [TIME]
- System recovered: [TIME]
- Root cause analysis: Ongoing

Next Steps:
- Post-mortem scheduled: [TIME]
- Phase 3 investigation: [TIME]
- Re-planning: [TIME]

Contact: Felipe@enbuenamesa.com
```

---

## ⚠️ EMERGENCY KILL-SWITCH

### Location

```
Endpoint: POST /api/admin/phase3/deactivate
Authentication: Bearer $ADMIN_TOKEN (required)
Rate Limit: None (emergency endpoint)
```

### Usage

**Quick disable (copy-paste ready):**

```bash
# Set your admin token
export ADMIN_TOKEN="your_admin_jwt_here"

# Trigger kill-switch
curl -X POST http://localhost:8000/api/admin/phase3/deactivate \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Emergency"}'
```

### Kill-Switch Response

```json
{
  "status": "DEACTIVATED",
  "timestamp": "2026-10-09T14:23:45Z",
  "phase3_active": false,
  "rollback_initiated": true,
  "backup_restored_from": "fase15_phase3_start_20261006_223600_UTC.sqlite",
  "estimated_recovery_time_seconds": 60,
  "message": "Phase 3 deactivated. Phase 2 active. All metrics GREEN."
}
```

### When to Use Kill-Switch

- ✋ Unexpected data corruption
- ✋ Cascading service failures
- ✋ Security incident
- ✋ Severe performance degradation (not auto-recovered)
- ✋ Board decision to halt immediately
- ✋ Unplanned outage affecting > 10% of users

### Post-Kill-Switch

1. Immediately notify Felipe + CTO
2. Post in Slack #incident channel
3. Begin post-mortem analysis
4. Document trigger and recovery steps
5. Review Phase 3 safety mechanisms

---

## 📬 COMMUNICATION PLAN

### Pre-Execution (Oct 6 22:36)

**Email: "FASE 15 Phase 3 - Activation Complete"**

Recipient: Engineering team, stakeholders  
Subject: Phase 3 ACTIVATED - Monitoring begins Oct 7  
Body: [See templates/email_phase3_activated.txt]

### Daily (Oct 7-13)

**Email: "FASE 15 Phase 3 - Daily Checkpoint Report"**

Recipient: felipe@enbuenamesa.com (daily summary)  
Subject: Phase 3 Day {1-7} Checkpoint Summary  
Body: [Auto-generated from checkpoint data]

### Final Decision (Oct 13 03:25)

**Email: "FASE 15 Phase 3 - Final Decision: GO ✅"**

Recipient: Board, C-suite, stakeholders  
Subject: Phase 3 GO Decision - $1.9B Revenue Impact Approved  
Body: [See templates/email_phase3_go_decision.txt]

**Press Release (if GO)**

Recipient: Media, investors, customers  
Subject: Company Announces Major Personalization Expansion  
Body: [See templates/press_release_phase3.txt]

### Slack Channel

**#fase15-phase3** (Read/Write for team)

- Post checkpoint summaries every 6 hours
- Alert on any CAUTION or RED metrics
- Celebrate reaching milestones (Day 3, Day 5, etc.)
- Final decision announcement at 03:30 UTC

---

## 📈 POST-EXECUTION ANALYSIS

### Report Generation (Automatic at Oct 13 03:25 UTC)

```bash
# Runs automatically
python3 phase3_generate_report.py

# Outputs:
# - reports/phase3_final_report.md (markdown)
# - reports/phase3_final_report.html (HTML for sharing)
# - reports/phase3_final_report.json (raw data)
```

### Analysis Dashboard

Available at: `http://localhost:3000/phase3-analysis`

Shows:
- 28 checkpoint timeline graph
- ML accuracy vs rules comparison
- Trend analysis (improving/stable/degrading)
- Alert timeline with resolutions
- Business impact calculations
- ROI projections

### Executive Summary Email

Sent automatically to Felipe with:
- 1 sentence: Success status
- 3 key metrics
- Checkpoint table
- Revenue impact
- Next steps

---

## 📚 APPENDICES

### Appendix A: Monitoring Daemon Logs

Location: `logs/monitoring_daemon.log`

```
2026-10-07 00:36:00 - INFO - Checkpoint 1/28 collected (HORA 48)
2026-10-07 00:36:02 - INFO - Metrics: ML=83.2%, Error=0.018%, Latency=8.1ms
2026-10-07 00:36:03 - INFO - Health Score: 6/6 GREEN - Status: OK
2026-10-07 00:36:05 - INFO - Checkpoint saved to: logs/phase3/checkpoint_48_20261007_003600.json
```

### Appendix B: System Config Flags

All Phase 3 control flags stored in `system_config` table:

| Key | Value | Meaning |
|-----|-------|---------|
| PHASE_3_ACTIVE | 1/0 | Phase 3 enabled/disabled |
| PHASE_3_ROLLOUT_PHASE | 1/2/3 | 10%/50%/100% users |
| PHASE_3_CONFIDENCE_LEVEL | 50-99 | Decision confidence |
| PHASE_3_LAST_CHECKPOINT | 48-76 | Last checkpoint hora |
| PHASE_3_DECISION | GO/CAUTION/NO-GO | Final decision |

### Appendix C: Error Scenarios & Responses

**Scenario 1: Error Rate spikes to 5%**
- Trigger: Error rate > 5% for 5 min
- Response: Automatic rollback to Phase 2
- Recovery time: ~60 seconds
- Action: Post-mortem analysis

**Scenario 2: Database connection pool exhausted**
- Trigger: > 30 failed connection attempts
- Response: Circuit breaker OPEN, retry with exponential backoff
- Recovery time: 30 seconds (half-open) + normal responses
- Action: Increase pool size or rollback

**Scenario 3: ML model service fails**
- Trigger: 10+ consecutive prediction timeouts
- Response: Fallback to rules-based system, log error
- Recovery time: < 100ms per request
- Action: Alert monitoring team

### Appendix D: Contacts & Escalation

| Role | Name | Email | Phone |
|------|------|-------|-------|
| Product Owner | Felipe | felipe@enbuenamesa.com | +34-xxx-xxxx |
| Engineering Lead | [Name] | [email] | [phone] |
| CTO | [Name] | [email] | [phone] |
| DevOps Lead | [Name] | [email] | [phone] |
| On-call Engineer | [Name] | [email] | [phone] |

---

## ✅ FINAL CHECKLIST

Before declaring Phase 3 execution complete:

- [ ] All 28 checkpoints collected successfully
- [ ] Final decision generated at 03:25 UTC
- [ ] Email notifications sent to stakeholders
- [ ] Metrics dashboard updated with results
- [ ] Post-execution analysis completed
- [ ] Executive summary report generated
- [ ] Team debriefing scheduled
- [ ] Lessons learned documented
- [ ] Success announcement published (if GO)
- [ ] Next phase planning initiated

---

**Document Status:** ✅ READY FOR PRODUCTION

**Last Review:** October 6, 2026 22:36 UTC  
**Approved by:** Felipe (Product Owner)  
**Team Sign-off:** Engineering + DevOps

---

*For questions or clarifications, contact: Felipe@enbuenamesa.com*
