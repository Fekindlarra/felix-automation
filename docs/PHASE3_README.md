# FASE 15 Phase 3: Production Execution Guide

## Overview

FASE 15 Phase 3 is the production deployment phase of the A/B testing and personalization framework. It represents the culmination of Phases 1 and 2, moving from 10% to 100% rollout of the winning variant with continuous health monitoring, automatic safeguards, and real-time decision making.

**Execution Window:** 24 hours (HORA 48-72)
**Checkpoints:** 13 monitoring points every 2 hours
**Success Criteria:** 5/6 health metrics GREEN for all checkpoints
**Automatic Rollback:** Triggered if <5/6 metrics fail

---

## Architecture Overview

### Core Components

#### 1. Circuit Breaker Pattern
Three independent circuit breakers protect critical services from cascading failures:

- **Database Breaker:** Protects SQLite connection pool
  - Threshold: 5 failures in 60 seconds
  - Timeout: 30 seconds recovery window
  - State: CLOSED (normal) → OPEN (fail fast) → HALF_OPEN (retry) → CLOSED

- **WebSocket Breaker:** Protects real-time event broadcasting
  - Threshold: 3 failures in 60 seconds
  - Timeout: 20 seconds recovery window
  - State monitoring: Connection drop = failure

- **Prediction Breaker:** Protects ML inference service
  - Threshold: 2 failures in 60 seconds
  - Timeout: 15 seconds recovery window
  - Fallback: Rules-based prediction if circuit open

#### 2. Rollback Manager
Continuous health monitoring with automatic decision logic:

```
Every 30 seconds:
1. Collect 6 metrics (database query, <1s)
2. Evaluate thresholds
3. Check circuit breaker states
4. Scan for CRITICAL alerts
5. Update decision state

Decision Logic:
- 6/6 metrics healthy → CONTINUE
- 5/6 metrics healthy → CAUTION
- <5/6 metrics healthy → NO-GO (prepare rollback)
- Any CRITICAL alert → rollback trigger
- Latency spike sustained 2 checks → rollback trigger
- Error rate spike sustained 5 min → rollback trigger
```

#### 3. Checkpoint System
13 scheduled checkpoints across 24-hour window:

| HORA | Time | Phase | Status |
|------|------|-------|--------|
| 48   | +0h  | 1: 10% rollout | Monitor |
| 50   | +2h  | 1: 10% rollout | Evaluate |
| 52   | +4h  | 1→2: Transition | **Phase advance if GO** |
| 54   | +6h  | 2: 50% rollout | Monitor |
| 56   | +8h  | 2: 50% rollout | Evaluate |
| 58   | +10h | 2→3: Transition | **Phase advance if GO** |
| 60   | +12h | 3: 100% rollout | Monitor |
| 62   | +14h | 3: 100% rollout | Evaluate |
| 64   | +16h | 3: 100% rollout | Stabilization |
| 66   | +18h | 3: 100% rollout | Stabilization |
| 68   | +20h | 3: 100% rollout | Stabilization |
| 70   | +22h | 3: 100% rollout | Final check |
| 72   | +24h | **FINAL** | **GO/CAUTION/NO-GO Decision** |

#### 4. Health Metrics (6 KPIs)

Each metric must exceed its target threshold for "healthy" status:

| Metric | Target | Status | Purpose |
|--------|--------|--------|---------|
| ML Accuracy | ≥78% | Must be healthy | Core ML model performance |
| Error Rate | <0.08% | Must be healthy | System stability |
| WebSocket Latency | <95ms | Must be healthy | Real-time performance |
| Predictions/Hour | ≥42 | Must be healthy | Volume throughput |
| Personalization Active | ≥140 | Must be healthy | Feature adoption |
| Active Tests | ≥8 | Must be healthy | Test portfolio health |

**Decision Thresholds:**
- **6/6 GREEN** → CONTINUE (proceed normally)
- **5/6 GREEN** → CAUTION (monitor closely, next checkpoint critical)
- **<5/6 GREEN** → NO-GO (trigger automatic rollback)

#### 5. Real-Time Dashboard

Live metrics dashboard updates every 5 seconds via WebSocket:

- **Real-Time Metrics Panel:** All 6 KPIs with live gauges
- **Test Lifecycle Stream:** Event log of test state changes
- **ML vs Rules Comparison:** Side-by-side accuracy tracking
- **Phase Rollout Progress:** Visual phase advancement (10% → 50% → 100%)
- **Alerts & Warnings:** Critical/warning/info alerts with timestamps

Dashboard automatically broadcasts Phase 3 events:
- `phase3:checkpoint_started`
- `phase3:metrics_collected`
- `phase3:decision_made`
- `phase3:phase_advanced` (when rollout escalates)
- `phase3:rollback_triggered` (if necessary)

#### 6. Kill-Switch & Feature Flags

Admin-controlled safety valve:

```
Endpoint: POST /api/admin/phase3/deactivate
Requires: Admin role + PHASE_3_ACTIVE feature flag = true
Response: Immediate Phase 3 shutdown
Fallback: All traffic reverts to Phase 2 logic
Timeline: <500ms to take effect globally
```

Feature flag stored in `system_config` table:
```sql
INSERT INTO system_config (key, value) 
VALUES ('PHASE_3_ACTIVE', 'true');
```

---

## Phase Advancement Logic

### Phase 1 → Phase 2 (HORA 52)
**Trigger:** First 2 checkpoints (HORA 48, 50) both return CONTINUE

```
IF checkpoint_48.decision == 'CONTINUE' AND
   checkpoint_50.decision == 'CONTINUE'
THEN
  escalate_rollout_percentage(from=10%, to=50%)
  personalization_variants.rollout_phase = 2
  BROADCAST phase3:phase_advanced event
  log_phase_transition(from=1, to=2, timestamp, hora=52)
```

### Phase 2 → Phase 3 (HORA 58)
**Trigger:** Checkpoints 50 and 56 both return CONTINUE

```
IF checkpoint_50.decision == 'CONTINUE' AND
   checkpoint_56.decision == 'CONTINUE' AND
   all_intermediate_checkpoints(52, 54) not 'NO-GO'
THEN
  escalate_rollout_percentage(from=50%, to=100%)
  personalization_variants.rollout_phase = 3
  BROADCAST phase3:phase_advanced event
  log_phase_transition(from=2, to=3, timestamp, hora=58)
```

### Final Decision (HORA 72)
**Evaluation:** All 13 checkpoints analyzed

```
GO Decision:
  IF all_13_checkpoints have decision == 'CONTINUE'
  AND no CRITICAL alerts in logs
  THEN status = 'SUCCESS'
  
CAUTION Decision:
  IF 11+ checkpoints are CONTINUE
  AND 1-2 checkpoints are CAUTION
  AND no rollbacks triggered
  THEN status = 'CAUTION' (continue monitoring 7 days)
  
NO-GO Decision (Auto Rollback):
  IF any checkpoint has decision == 'NO-GO'
  THEN status = 'ROLLED_BACK'
  AND restore_from_backup()
  AND revert_to_phase_2_logic()
```

---

## Automatic Rollback Triggers

Phase 3 will **automatically rollback** if any of these conditions are met:

### 1. Metric Threshold Failure
```
IF metrics_met < 5 for any checkpoint
THEN trigger_rollback("insufficient_healthy_metrics")
```

### 2. Latency Spike
```
IF websocket_latency > 200ms for 2 consecutive checkpoints
THEN trigger_rollback("latency_spike")
```

### 3. Error Rate Spike
```
IF error_rate > 0.5% sustained for 5 minutes
THEN trigger_rollback("error_rate_spike")
```

### 4. Critical Alert
```
IF alert.severity == 'CRITICAL'
THEN trigger_rollback("critical_alert")
AND send_notification("Phase 3 Rollback Triggered", alert_details)
```

### 5. Database Connection Loss
```
IF database_breaker.state == 'OPEN' for >60 seconds
THEN trigger_rollback("database_unavailable")
```

### 6. ML Model Failure
```
IF prediction_breaker.state == 'OPEN' for >60 seconds
THEN trigger_rollback("prediction_service_unavailable")
```

### Rollback Process
```
1. Disable PHASE_3_ACTIVE feature flag
2. Revert all clients to Phase 2 logic
3. Restore database from pre-Phase3 backup
4. Log rollback event with trigger and timestamp
5. Broadcast phase3:rollback_triggered event
6. Send alerts to on-call team
7. Archive Phase 3 checkpoint logs for analysis
```

**Rollback Time to Effect:** <1 second for feature flag, 5-30 seconds for database restore

---

## Execution Prerequisites

### Pre-Flight Checks (5 required, all must PASS)

Before Phase 3 activation, verify:

1. **Database Connection**
   - SQLite connection succeeds
   - All 6 required tables exist and are accessible
   - Database file is readable/writable

2. **Phase 2 Metrics Healthy**
   - Phase 2 has run for ≥24 hours
   - All 6 metrics consistently GREEN for last 24h
   - Error rate <0.1% sustained
   - No CRITICAL alerts in Phase 2 logs

3. **Database Integrity**
   - Schema validation passes
   - All indices present and valid
   - Foreign key constraints verified
   - No data corruption detected (PRAGMA integrity_check)

4. **Recent Backups**
   - Latest backup <2 hours old
   - Backup file verified readable
   - Restoration test successful (test restore to temp db)

5. **System Components Healthy**
   - Circuit breakers initialized and in CLOSED state
   - WebSocket manager connects successfully
   - Prediction service available
   - Monitoring daemon ready to run
   - All dependencies importable

### Environment Setup

```bash
# Set environment variables
export FASE15_PHASE3_ENABLED=true
export PHASE_3_ACTIVE=true
export CHECKPOINT_LOG_DIR=./logs/phase3
export BACKUP_DIR=./data/backups

# Create directories
mkdir -p logs/phase3
mkdir -p data/backups

# Verify database
python3 -c "from backend.db import get_db; db = get_db(); print('✓ Database connected')"

# Test circuit breakers
python3 -c "from backend.circuit_breaker import get_database_breaker; cb = get_database_breaker(); print(f'✓ Database breaker: {cb.get_state()}')"
```

---

## Monitoring During Execution

### Real-Time Dashboard
- **URL:** `http://localhost:8000/phase3/dashboard`
- **Refresh Rate:** Every 5 seconds via WebSocket
- **Alerts Panel:** Displays critical/warning/info in real-time
- **Export:** Metrics can be downloaded as CSV or PDF

### Checkpoint Logs
Located in `logs/phase3/checkpoint_HORA_*.json`:

```json
{
  "hora": 48,
  "timestamp": "2026-10-06T22:00:00Z",
  "metrics": {
    "ml_accuracy": 0.835,
    "error_rate": 0.00017,
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

### Prometheus Metrics
Custom Phase 3 metrics exported to Prometheus:

- `fase15_phase3_ml_accuracy` - ML model accuracy percentage
- `fase15_phase3_error_rate` - System error rate percentage
- `fase15_phase3_websocket_latency` - WebSocket latency in ms
- `fase15_phase3_predictions_per_hour` - Predictions per hour
- `fase15_phase3_personalization_active` - Active personalization instances
- `fase15_phase3_active_tests` - Number of active tests
- `fase15_phase3_checkpoint_status` - Latest checkpoint decision (1=CONTINUE, 0=CAUTION, -1=ROLLBACK)

### Alerting Rules

Alert rules configured in Prometheus for:
- **CRITICAL:** Any metric threshold exceeded
- **WARNING:** Metric approaching threshold
- **INFO:** Phase advancement detected
- **INFO:** Checkpoint completed

---

## Success Criteria & Expected Outcomes

### GO Status (All Checkpoints CONTINUE)
- ✅ All 13 checkpoints have decision = 'CONTINUE'
- ✅ 6/6 metrics GREEN throughout entire 24-hour window
- ✅ No circuit breakers triggered
- ✅ No CRITICAL alerts in logs
- ✅ Phase advancement: 10% → 50% → 100% successful
- ✅ Dashboard updated in real-time every 5 seconds
- ✅ Checkpoints saved and archived

**Outcome:** Phase 3 marked as SUCCESS, campaign live at 100% scale

### CAUTION Status (Mostly CONTINUE, 1-2 CAUTION)
- ⚠️  11+ checkpoints = CONTINUE, 1-2 = CAUTION
- ⚠️  No NO-GO decisions or rollbacks triggered
- ⚠️  All phases advanced successfully (10% → 50% → 100%)
- ⚠️  Phase 3 remains active but under observation

**Outcome:** Phase 3 marked as CAUTION, continue monitoring for 7 days before declaring full success

### NO-GO Status (Any NO-GO, Auto Rollback)
- ❌ Any checkpoint returns decision = 'NO-GO'
- ❌ Automatic rollback triggered
- ❌ Database restored from backup
- ❌ Phase 3 feature flag disabled
- ❌ All traffic reverts to Phase 2

**Outcome:** Phase 3 marked as ROLLED_BACK, analysis conducted, improvements planned for Phase 4

---

## Operational Contacts & Escalation

| Role | Contact | Availability |
|------|---------|--------------|
| Phase 3 Owner | Felipe | 24/7 during execution |
| On-Call Engineer | [Team Schedule] | Rotating on-call |
| Database Admin | [DBA Name] | Business hours + on-call |
| ML Engineer | [ML Team] | Business hours |

**Escalation Path:**
1. Automated alerts sent to on-call engineer via Slack/Email
2. If no response within 5 minutes, escalate to Phase 3 Owner
3. If critical rollback needed, decision can be made autonomously by alert system
4. Post-mortem required for any CAUTION or NO-GO outcome

---

## Post-Execution Analysis

### Final Report Generation
After HORA 72, automated report generation:

```bash
python3 phase3_generate_report.py
# Outputs:
# - reports/phase3_final_report.md (markdown)
# - reports/phase3_final_report.html (formatted)
# - reports/phase3_final_report.json (data)
```

### Business Impact Calculation
Report includes:
- ML accuracy average across 13 checkpoints
- Error rate average and trend
- Latency improvements (ms reduction)
- Conversion lift estimation (30-50% expected)
- Revenue impact calculation
- ROI analysis

### Executive Summary Email
Automated email sent to leadership:
- Subject: "FASE 15 Phase 3 Complete - [GO/CAUTION/ROLLED_BACK]"
- Body: Key metrics, phase advancement timeline, business impact
- Attachment: PDF of final report
- Dashboard: Link to 24-hour metrics archive

---

## Troubleshooting Guide

### Common Issues & Resolution

**Issue: Checkpoint collection fails**
```
Error: "Failed to collect metrics at HORA 52"
Check:
1. Database connection: Is SQLite accessible?
2. Metrics availability: Are all 6 metrics queryable?
3. Circuit breaker state: Is database_breaker CLOSED?
Resolution: See "Troubleshooting" section in operations runbook
```

**Issue: Dashboard shows disconnected**
```
Error: "WebSocket connection lost"
Check:
1. Network connectivity: Can client reach WebSocket server?
2. WebSocket manager: Is it running? (Check logs)
3. Browser console: Any JS errors?
Resolution: Refresh dashboard, check WebSocket logs in backend
```

**Issue: Phase advancement stalled**
```
Error: "Phase did not advance at HORA 52"
Check:
1. Checkpoint decisions: Were they both CONTINUE?
2. Rollout engine: Is personalization_engine processing updates?
3. Database write: Are rollout_phase updates committed?
Resolution: Manual phase advancement via admin endpoint (if authorized)
```

**Issue: Manual rollback needed (Emergency)**
```
Action: Call kill-switch endpoint
curl -X POST http://localhost:8000/api/admin/phase3/deactivate \
  -H "Authorization: Bearer <admin_token>"

Verification:
1. Feature flag disabled: SELECT * FROM system_config WHERE key='PHASE_3_ACTIVE'
2. Traffic reverted: Check logs for "Phase 3 disabled"
3. Clients back to Phase 2: Verify variant assignments in db

Post-Rollback: Contact Phase 3 Owner for analysis
```

---

## Reference Files

- **Activation Runbook:** `docs/RUNBOOK_PHASE3_ACTIVATION.md`
- **Monitoring Runbook:** `docs/RUNBOOK_PHASE3_MONITORING.md`
- **Rollback Procedures:** `docs/RUNBOOK_PHASE3_ROLLBACK.md`
- **API Documentation:** `docs/API_PHASE3_ENDPOINTS.md`
- **Team Onboarding:** `docs/ONBOARDING_PHASE3.md`
- **Test Suite:** `tests/test_*.py` and `tests/integration/test_*.py`

---

**Last Updated:** October 6, 2026  
**Status:** Production Ready  
**Version:** 1.0
