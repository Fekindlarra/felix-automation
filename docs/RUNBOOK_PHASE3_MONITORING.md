# RUNBOOK: Phase 3 Monitoring & Checkpoint Procedures

## Overview

This runbook provides instructions for monitoring Phase 3 execution during the 24-hour checkpoint window (HORA 48-72). Phase 3 runs continuously with checkpoint evaluations every 2 hours. This document covers normal operations, interpreting results, responding to alerts, and manual interventions if needed.

**Execution Window:** 24 hours  
**Checkpoints:** 13 total, every 2 hours (HORA 48, 50, 52, ..., 72)  
**Automation Level:** 99% automated, 1% manual review  
**Decision Points:** Phase advancement at HORA 52 and HORA 58, final decision at HORA 72

---

## Monitoring Dashboard

### Access Dashboard

```bash
# Open in browser
http://localhost:8000/phase3/dashboard

# Alternative URLs
http://localhost:8000/phase3/realtime_dashboard
http://127.0.0.1:8000/phase3/dashboard
```

**Dashboard Features:**

1. **Real-Time Metrics Panel** (Top)
   - 6 KPIs displayed with current values
   - Color coding: GREEN (healthy), YELLOW (warning), RED (critical)
   - Gauges update every 5 seconds via WebSocket

2. **Status Indicator** (Top-Right)
   - Shows number of healthy metrics (e.g., "6/6 GREEN")
   - Changes color: Green (6/6) → Yellow (5/6) → Red (<5/6)

3. **Checkpoint Timeline** (Middle)
   - Chronological list of all past checkpoints
   - Shows HORA, timestamp, decision (CONTINUE/CAUTION/NO-GO)
   - Click to expand and view detailed metrics

4. **Alerts Panel** (Right)
   - CRITICAL alerts highlighted in red
   - WARNING alerts in yellow
   - INFO alerts in blue
   - Sortable by severity and time

5. **Phase Progression** (Bottom)
   - Visual display of rollout percentage (10% → 50% → 100%)
   - Shows current phase and when transitions occurred

### Dashboard Navigation

| Section | Purpose | Refresh |
|---------|---------|---------|
| Real-Time Metrics | Live KPI values | 5 sec |
| Status Indicator | Overall health (6/6) | 5 sec |
| Checkpoint Timeline | Historical decisions | 2 min |
| Alerts Panel | Active alerts | 1 sec |
| Phase Progression | Rollout status | 2 min |

**Keyboard Shortcuts:**
- `R` - Refresh all metrics manually
- `P` - Pause auto-updates
- `E` - Export metrics to CSV
- `?` - Show keyboard shortcuts

---

## Checkpoint Execution

### Automatic Checkpoint Schedule

Checkpoints execute automatically every 2 hours:

| HORA | Time | Phase | What Happens |
|------|------|-------|--------------|
| 48 | +0h | 1: 10% | First metrics collection & evaluation |
| 50 | +2h | 1: 10% | Second collection, determine Phase 1 GO/CAUTION |
| 52 | +4h | **1→2** | **Phase advance if 48+50 both CONTINUE** |
| 54 | +6h | 2: 50% | Continue monitoring Phase 2 |
| 56 | +8h | 2: 50% | Evaluate Phase 2 readiness |
| 58 | +10h | **2→3** | **Phase advance if 50+56 both CONTINUE** |
| 60 | +12h | 3: 100% | Stabilization at 100% scale |
| 62 | +14h | 3: 100% | Verify stability continues |
| 64 | +16h | 3: 100% | Ensure no regressions |
| 66 | +18h | 3: 100% | Final checks |
| 68 | +20h | 3: 100% | Pre-completion validation |
| 70 | +22h | 3: 100% | Last checkpoint before final decision |
| 72 | +24h | **FINAL** | **Final GO/CAUTION/NO-GO decision** |

### What Happens at Each Checkpoint

**Checkpoint Execution Steps (Automated):**

```
1. Collect Metrics (30 seconds)
   └─ Query 6 KPI values from backend_metrics_collector table
   └─ Calculate averages for each metric
   └─ Store raw values for audit trail

2. Evaluate Thresholds (5 seconds)
   └─ Compare each metric against target
   └─ Count how many metrics are "healthy"
   └─ Determine status: CONTINUE (6/6) / CAUTION (5/6) / NO-GO (<5/6)

3. Check Circuit Breakers (2 seconds)
   └─ Database breaker state
   └─ WebSocket breaker state
   └─ Prediction breaker state
   └─ Any OPEN breaker logs warning

4. Scan Alerts (5 seconds)
   └─ Check for CRITICAL alerts in last 2 hours
   └─ If CRITICAL found: escalate to NO-GO immediately

5. Decision Making (1 second)
   └─ Apply decision logic based on step 2
   └─ Apply rollback triggers if needed
   └─ Generate checkpoint JSON file

6. Broadcast Event (1 second)
   └─ Send WebSocket event to dashboard
   └─ Notify monitoring team
   └─ Archive to checkpoint log

7. Phase Advancement Check (5 seconds)
   └─ At HORA 52: Check if 48+50 both CONTINUE → escalate to 50%
   └─ At HORA 58: Check if 50+56 both CONTINUE → escalate to 100%
   └─ At HORA 72: Calculate final decision

Total Time: ~50 seconds per checkpoint
```

### Checkpoint Output Format

Each checkpoint creates a JSON file at `logs/phase3/checkpoint_HORA_XX.json`:

```json
{
  "hora": 52,
  "timestamp": "2026-10-06T22:00:00Z",
  "metrics": {
    "ml_accuracy": 0.835,
    "error_rate": 0.00017,
    "websocket_latency": 8,
    "predictions_hour": 48,
    "personalization_active": 150,
    "active_tests": 9
  },
  "thresholds": {
    "ml_accuracy": {"target": 0.78, "healthy": true},
    "error_rate": {"target": 0.0008, "healthy": true},
    "websocket_latency": {"target": 95, "healthy": true},
    "predictions_hour": {"target": 42, "healthy": true},
    "personalization_active": {"target": 140, "healthy": true},
    "active_tests": {"target": 8, "healthy": true}
  },
  "status": "6/6 GREEN",
  "metrics_met": 6,
  "unhealthy_metrics": [],
  "decision": "CONTINUE",
  "circuit_breakers": {
    "database": "CLOSED",
    "websocket": "CLOSED",
    "prediction": "CLOSED"
  },
  "alerts": [],
  "notes": "All metrics excellent, phase 1 complete",
  "phase_advancement": {
    "from_phase": 1,
    "to_phase": 2,
    "triggered": true,
    "reason": "CONTINUE decision at HORA 52 with HORA 50 also CONTINUE"
  }
}
```

---

## Monitoring During Checkpoints

### Real-Time Monitoring (Every 2 Hours)

At each checkpoint time, perform these manual checks:

**T-5 minutes (Before checkpoint):**
- [ ] Dashboard is loaded and connected (show "Connected" status)
- [ ] All 6 metrics showing values (not null/loading)
- [ ] No unusual alerts in alerts panel

**T+0 (Checkpoint executes):**
- [ ] Dashboard shows "Checkpoint in progress" message
- [ ] Real-time metric updates continue flowing
- [ ] Status indicator remains visible

**T+5 minutes (After checkpoint):**
- [ ] Checkpoint appears in timeline
- [ ] Decision clearly visible (CONTINUE/CAUTION/NO-GO)
- [ ] Metrics snapshot saved to checkpoint JSON
- [ ] WebSocket event broadcast confirmed in logs

**T+10 minutes (Review decision):**
- [ ] Click checkpoint to expand and view metrics
- [ ] Verify status matches decision (e.g., 6/6 GREEN → CONTINUE)
- [ ] Note any red-flag metrics or warnings
- [ ] Check notes field for context

### What to Watch For

**Green Lights (Everything Good):**
- ✅ All 6 metrics show GREEN
- ✅ Status shows "6/6 GREEN"
- ✅ Decision is "CONTINUE"
- ✅ No alerts in alerts panel
- ✅ Dashboard updates smoothly every 5 seconds

**Yellow Flags (Needs Review):**
- ⚠️  One metric showing YELLOW (approaching threshold)
- ⚠️  Status shows "5/6 GREEN" → decision "CAUTION"
- ⚠️  One or two INFO alerts
- ⚠️  Latency showing slight increase but <95ms
- ⚠️  Error rate showing slight increase but <0.08%

**Red Flags (Action Needed):**
- 🔴 Any metric showing RED
- 🔴 Status shows "<5/6 GREEN" → decision "NO-GO"
- 🔴 CRITICAL alert in alerts panel
- 🔴 Circuit breaker showing OPEN or HALF_OPEN
- 🔴 Dashboard disconnects or stops updating

---

## Decision Interpretation

### CONTINUE (6/6 Metrics Healthy)

**Meaning:** Phase is performing excellently, no concerns

```
What you'll see:
- Status: "6/6 GREEN"
- Decision: "CONTINUE"
- All metrics showing green
- No alerts or red flags

Actions:
- Continue normal monitoring
- No manual intervention needed
- System will proceed to next checkpoint

At Phase Advancement Points (HORA 52, 58):
- System automatically escalates rollout percentage
- Dashboard shows phase progression update
- No operator action required
```

**Example Metrics:**
```
ML Accuracy:         83.5% (target: ≥78%) ✓
Error Rate:          0.017% (target: <0.08%) ✓
WebSocket Latency:   8ms (target: <95ms) ✓
Predictions/Hour:    48 (target: ≥42) ✓
Personalization:     150 (target: ≥140) ✓
Active Tests:        9 (target: ≥8) ✓
```

### CAUTION (5/6 Metrics Healthy)

**Meaning:** One metric is unhealthy, but not critical; requires close monitoring

```
What you'll see:
- Status: "5/6 GREEN" with one YELLOW
- Decision: "CAUTION"
- One metric showing yellow or red
- One or more WARNING alerts possible

Actions:
- Increase monitoring frequency to every 30 minutes
- Investigate which metric is failing
- Check if trend is worsening or stable
- At next checkpoint, if CONTINUE, no action needed
- If CAUTION repeats, escalate to Phase 3 Owner

Critical: Do NOT manually intervene unless decision changes to NO-GO
```

**Example Scenario:**
```
ML Accuracy:         75.2% (target: ≥78%) ✗ UNHEALTHY
Error Rate:          0.017% (target: <0.08%) ✓
WebSocket Latency:   12ms (target: <95ms) ✓
Predictions/Hour:    48 (target: ≥42) ✓
Personalization:     150 (target: ≥140) ✓
Active Tests:        9 (target: ≥8) ✓

Status: 5/6 GREEN, Decision: CAUTION

What to do:
1. Click on ML Accuracy metric for trend
2. Check if accuracy is improving or worsening
3. Set alarm for next checkpoint (2 hours)
4. If next checkpoint is also CAUTION: contact Felipe
5. If next checkpoint is CONTINUE: system recovers, continue monitoring
```

### NO-GO (<5/6 Metrics Healthy)

**Meaning:** Multiple metrics failing or critical alert; automatic rollback initiated

```
What you'll see:
- Status: "<5/6 GREEN" (red background)
- Decision: "NO-GO"
- Multiple metrics showing red
- CRITICAL alert in alerts panel
- Dashboard shows "ROLLBACK IN PROGRESS"

Actions:
- Automatic rollback executes within 30 seconds
- Monitor rollback progress in logs
- DO NOT manually intervene
- Phase 3 feature flag disabled automatically
- System reverts to Phase 2 automatically

After Rollback:
1. Confirm system reverted (check logs)
2. Verify traffic back to Phase 2 logic
3. Notify Phase 3 Owner immediately
4. Archive Phase 3 logs for post-mortem
5. Wait for instructions (may restart at different time)
```

**Example Scenario:**
```
ML Accuracy:         72.1% (target: ≥78%) ✗ UNHEALTHY
Error Rate:          0.12% (target: <0.08%) ✗ UNHEALTHY
WebSocket Latency:   150ms (target: <95ms) ✗ UNHEALTHY
Predictions/Hour:    35 (target: ≥42) ✗ UNHEALTHY
Personalization:     95 (target: ≥140) ✗ UNHEALTHY
Active Tests:        6 (target: ≥8) ✗ UNHEALTHY

Status: 0/6 GREEN (critical), Decision: NO-GO

Automatic Response (IMMEDIATE):
1. Rollback triggered automatically
2. PHASE_3_ACTIVE flag set to 'false'
3. All traffic reverted to Phase 2
4. Database restored from backup
5. Alerts sent to on-call engineer
```

---

## Responding to Alerts

### Alert Types & Severity

| Severity | Color | Response Time | Action |
|----------|-------|----------------|--------|
| CRITICAL | Red | Immediate (1 min) | Review, escalate if needed |
| WARNING | Yellow | 10 minutes | Investigate, document |
| INFO | Blue | No action | Log, archive |

### Common Alerts During Phase 3

**CRITICAL Alerts:**

1. **"Database Connection Lost"**
   - Symptom: Cannot query metrics
   - Cause: Database unavailable or crashed
   - Action:
     ```bash
     # Check database
     sqlite3 data/db.sqlite3 ".tables"
     
     # If no output, database is corrupted
     # Trigger manual rollback (see Rollback section)
     
     # Notify Phase 3 Owner
     echo "CRITICAL: Database unavailable" | mail -s "Phase 3 Alert" felipe@enbuenamesa.com
     ```

2. **"Prediction Service Unavailable"**
   - Symptom: ML predictions failing
   - Cause: ML service crashed or circuit breaker opened
   - Action:
     ```bash
     # Check if prediction service is running
     ps aux | grep prediction
     
     # Check prediction breaker state
     python3 -c "
     from backend.circuit_breaker import get_prediction_breaker
     print(f'Prediction Breaker: {get_prediction_breaker().get_state()}')
     "
     
     # If OPEN for >60 seconds: automatic rollback will trigger
     # Wait 30 seconds before taking action
     ```

3. **"Latency Spike Detected"**
   - Symptom: WebSocket latency >200ms
   - Cause: Network congestion or resource exhaustion
   - Action:
     ```bash
     # Check current latency
     grep "websocket_latency" logs/phase3/checkpoint_*.json | tail -3
     
     # If sustained >200ms for 2 checks: automatic rollback
     # If spiking but recovering: continue monitoring
     
     # Check system resources
     top -b -n 1 | head -20  # CPU/memory usage
     ```

4. **"Error Rate Spike"**
   - Symptom: Error rate >0.5%
   - Cause: Application issues or external dependency failure
   - Action:
     ```bash
     # Check backend logs for errors
     tail -100 logs/backend.log | grep ERROR
     
     # Identify error source
     grep -E "exception|traceback" logs/backend.log | tail -10
     
     # If sustained >0.5% for 5 minutes: automatic rollback
     # If spike is isolated: continue monitoring
     ```

**WARNING Alerts:**

1. **"Metric Approaching Threshold"**
   - Symptom: ML accuracy 76-78% (approaching 78% threshold)
   - Action: Increase monitoring frequency, watch next checkpoint closely

2. **"Personalization Adoption Low"**
   - Symptom: <150 active personalization instances
   - Action: Check if feature is enabled, verify rollout percentage

3. **"Test Portfolio Degrading"**
   - Symptom: <10 active tests
   - Action: Check if tests completed, verify test creation still working

**INFO Alerts:**

1. **"Phase Advanced to 50%"**
   - Informational only, no action needed

2. **"Checkpoint Completed"**
   - Informational only, check dashboard to review

3. **"System Health Check Passed"**
   - Informational only, good indicator

---

## Manual Checkpoint Review

If you want to manually inspect a checkpoint that just completed:

```bash
# List all checkpoints
ls -la logs/phase3/checkpoint_*.json | head -20

# View latest checkpoint
cat logs/phase3/checkpoint_HORA_52.json | python3 -m json.tool

# Parse specific field
python3 -c "
import json

with open('logs/phase3/checkpoint_HORA_52.json') as f:
    checkpoint = json.load(f)
    
print(f'HORA: {checkpoint[\"hora\"]}')
print(f'Status: {checkpoint[\"status\"]}')
print(f'Decision: {checkpoint[\"decision\"]}')
print(f'Metrics Met: {checkpoint[\"metrics_met\"]}/6')

for metric, value in checkpoint['metrics'].items():
    threshold = checkpoint['thresholds'][metric]
    healthy = threshold['healthy']
    status = '✓' if healthy else '✗'
    print(f'  {status} {metric}: {value} (target: {threshold[\"target\"]})')
"

# Compare consecutive checkpoints
python3 -c "
import json

checkpoints = [48, 50, 52]

for hora in checkpoints:
    with open(f'logs/phase3/checkpoint_HORA_{hora}.json') as f:
        cp = json.load(f)
        print(f'HORA {cp[\"hora\"]}: {cp[\"status\"]} → {cp[\"decision\"]}')
"
```

---

## Phase Advancement Monitoring

### HORA 52: Phase 1 → Phase 2 Transition

**What to watch:**

```
HORA 48 Checkpoint Complete
↓
Check: Is decision = "CONTINUE"? 
  YES ✓ → Proceed
  NO ✗ → Check HORA 50
  
HORA 50 Checkpoint Complete  
↓
Check: Is decision = "CONTINUE"?
  YES ✓ + HORA 48 was CONTINUE → PHASE ADVANCE!
  NO ✗ → No phase advance, continue Phase 1
```

**At HORA 52:**

If both checkpoints returned CONTINUE:
- [ ] Dashboard shows "Phase Progression: 10% → 50%"
- [ ] Checkpoint JSON shows `"phase_advancement": {"from_phase": 1, "to_phase": 2}`
- [ ] `personalization_variants.rollout_phase` updated to 2 in database
- [ ] Next 6 hours (HORA 52-58) run Phase 2 at 50% rollout

```bash
# Verify phase advancement occurred
python3 -c "
import json

with open('logs/phase3/checkpoint_HORA_52.json') as f:
    cp = json.load(f)
    
if cp.get('phase_advancement', {}).get('triggered'):
    print(f'✓ Phase advanced: {cp[\"phase_advancement\"][\"from_phase\"]} → {cp[\"phase_advancement\"][\"to_phase\"]}')
    print(f'  Reason: {cp[\"phase_advancement\"][\"reason\"]}')
else:
    print('✗ Phase advancement did not trigger')
    print('  Check HORA 50 and 52 decisions')
"
```

### HORA 58: Phase 2 → Phase 3 Transition

Same logic as above, but comparing HORA 50 and HORA 56:

```
HORA 50 decision = CONTINUE? 
  + HORA 56 decision = CONTINUE?
  → YES: PHASE ADVANCE to Phase 3 (100%)
  → NO: Continue Phase 2
```

At HORA 58, if phase advances:
- [ ] Dashboard shows "Phase Progression: 50% → 100%"
- [ ] All new clients now receive winning variant
- [ ] Final 6 hours (HORA 58-72) measure success at full scale

---

## Escalation Procedures

### When to Escalate to Phase 3 Owner

**Immediate Escalation (Call/Text):**
- Any CRITICAL alert
- 2 consecutive CAUTION decisions
- Circuit breaker OPEN for >30 seconds
- Latency spike >200ms sustained
- Database unavailable

**Email Escalation (30-minute response):**
- Single CAUTION decision (informational)
- Metric trending toward threshold
- Unusual but non-critical alert
- Any question about interpretation

**No Escalation Needed:**
- All checkpoints CONTINUE
- No alerts
- Phase advancing on schedule
- Everything running nominally

### Escalation Contact

```bash
# Primary: Felipe
EMAIL: felipe@enbuenamesa.com
PHONE: [Phase 3 Owner contact]
AVAILABILITY: 24/7 during Phase 3 execution

# On-Call Team (if Felipe unavailable)
SLACK: #phase3-alerts
EMAIL: oncall@team.com

# Emergency (immediate rollback needed)
KILL-SWITCH ENDPOINT: POST /api/admin/phase3/deactivate
```

**Escalation Email Template:**

```
Subject: Phase 3 Alert - [CRITICAL/WARNING/INFO] - HORA XX

HORA: XX
Time: [timestamp]
Decision: [CONTINUE/CAUTION/NO-GO]
Status: [X/6 GREEN]

Critical Metric(s):
- [Metric]: [Value] (target: [threshold])

Context:
[2-3 sentences explaining the situation]

Action Taken:
[What have you already done]

Recommended Action:
[What you think should happen next]
```

---

## Troubleshooting During Monitoring

### Issue: Dashboard Disconnects

```bash
# Check WebSocket connection
python3 -c "
from backend.websocket_manager import get_connection_manager
ws = get_connection_manager()
print(f'Active connections: {len(ws.active_connections) if ws else 0}')
"

# Check backend logs
grep -i "websocket" logs/backend.log | tail -20

# Restart WebSocket if needed
pkill -f "websocket_manager"
# (It will restart automatically)

# Refresh browser tab
# Click refresh button in dashboard
```

### Issue: Checkpoint Not Appearing

```bash
# Check if monitoring daemon is running
ps aux | grep monitoring_daemon

# Check daemon logs
tail -50 logs/phase3_monitoring.log

# Check if checkpoint file was created
ls -la logs/phase3/checkpoint_HORA_XX.json

# If file exists but not showing in dashboard:
# - Refresh browser page (Ctrl+R)
# - Check browser console for JS errors (F12)
# - Check WebSocket connection status
```

### Issue: Metric Showing Null

```bash
# Check if metric collector is running
python3 -c "
from backend.monitoring import get_metrics_collector
mc = get_metrics_collector()
print('Metrics Collector: Available')
"

# Check database table
sqlite3 data/db.sqlite3 "SELECT * FROM backend_metrics_collector LIMIT 5"

# Check for any errors in metric collection
grep -i "metric" logs/backend.log | grep -i "error" | tail -10
```

### Issue: Alert Not Triggering

```bash
# Check alert system
python3 -c "
from backend.alerting_system import get_alert_manager
am = get_alert_manager()
alerts = am.get_active_alerts()
print(f'Active alerts: {len(alerts)}')
for alert in alerts:
    print(f'  {alert[\"severity\"]}: {alert[\"message\"]}')
"

# Check if metric is actually unhealthy
python3 -c "
from backend.rollback_manager import RollbackManager
rm = RollbackManager()
# Get current metrics and check health
"

# Alerts may be suppressed if already fired recently
# Check alert history
grep "alert" logs/alerting.log | tail -20
```

---

## End of Checkpoint Window (HORA 72)

### Final Checkpoint & Decision

At HORA 72 (24 hours), the final checkpoint executes with special logic:

```bash
# Monitor final checkpoint
tail -f logs/phase3_monitoring.log | grep "HORA.*72"

# Wait for checkpoint file
ls -la logs/phase3/checkpoint_HORA_72.json

# View final decision
cat logs/phase3/checkpoint_HORA_72.json | python3 -m json.tool
```

**Final Decision Determination:**

```
If all_13_checkpoints == CONTINUE:
  → Final Status: SUCCESS (Phase 3 complete, campaign live 100%)
  
Elif 11+ CONTINUE, 1-2 CAUTION, 0 NO-GO:
  → Final Status: CAUTION (Phase 3 continues, observe 7 days)
  
Elif any NO-GO or CRITICAL_ALERT:
  → Final Status: ROLLED_BACK (automatic)
  
Else:
  → Final Status: UNCLEAR (manual review required)
```

**After HORA 72:**
- [ ] Final report generated automatically
- [ ] Executive summary email sent
- [ ] Dashboard archived for analysis
- [ ] Checkpoints locked (no further updates)
- [ ] Monitoring daemon stopped

---

**Document Version:** 1.0  
**Last Updated:** October 6, 2026  
**Status:** Production Ready
