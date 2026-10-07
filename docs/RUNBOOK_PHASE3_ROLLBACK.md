# RUNBOOK: Phase 3 Rollback Procedures

## Overview

This runbook provides procedures for rollback scenarios during Phase 3 execution. Rollback can occur automatically (triggered by system conditions) or manually (by administrator action). This document covers both scenarios, verification procedures, and post-rollback analysis.

**Rollback Trigger Latency:** <500ms (feature flag disable to full effect)  
**Database Restore Time:** 5-30 seconds (depends on backup size)  
**Total Time to Stable State:** <60 seconds  
**Rollback Scope:** All Phase 3 features disabled, Phase 2 logic restored

---

## Automatic Rollback Triggers

Phase 3 will automatically rollback if any condition is met:

### 1. Insufficient Healthy Metrics (<5/6)

```
Trigger: checkpoint.metrics_met < 5

What Happens:
1. Rollback manager detects <5/6 healthy at checkpoint evaluation
2. Sets decision = 'NO-GO' 
3. Initiates automatic rollback sequence

Detection Time: At next 2-hour checkpoint (or within 2 hours if mid-checkpoint)
Example: HORA 54 checkpoint finds only 3/6 healthy → immediate rollback
```

### 2. Latency Spike (>200ms sustained)

```
Trigger: websocket_latency > 200ms for 2 consecutive checks

What Happens:
1. Monitoring daemon tracks latency every 30 seconds
2. If latency >200ms at check N and check N+1:
   - Sets latency_spike_detected = True
   - Initates rollback after 30 second confirmation

Detection Time: 60+ seconds from spike beginning
Example: 
  Check 1: latency=210ms (flag raised)
  Check 2: latency=205ms (confirmed, rollback initiated)
```

### 3. Error Rate Spike (>0.5% sustained)

```
Trigger: error_rate > 0.005 sustained for 5 minutes

What Happens:
1. Monitoring daemon tracks error rate every 60 seconds
2. If error_rate > 0.5% persists for 5+ minutes:
   - Sets error_spike_detected = True
   - Initiates rollback

Detection Time: 300+ seconds from spike beginning
Example:
  Min 1: error_rate=0.6% (flag raised)
  Min 2: error_rate=0.7% (continues)
  Min 3: error_rate=0.65% (continues)
  Min 4: error_rate=0.8% (continues)
  Min 5: error_rate=0.75% (confirmed, rollback initiated)
```

### 4. Critical Alert Received

```
Trigger: Any alert with severity='CRITICAL'

What Happens:
1. Alert system detects CRITICAL alert
2. Alert manager immediately triggers rollback
3. Does not wait for next checkpoint

Detection Time: <10 seconds from alert generation
Example: 
  - Database connection lost → CRITICAL alert → immediate rollback
  - Prediction service unavailable → CRITICAL alert → immediate rollback
  - Circuit breaker permanently OPEN → CRITICAL alert → immediate rollback
```

### 5. Database Connection Loss

```
Trigger: database_breaker.state == OPEN for >60 seconds

What Happens:
1. Circuit breaker tracks database failure count
2. After 60 seconds in OPEN state:
   - Database unavailable confirmed
   - Initiates automatic rollback
3. Database operations bypass and fallback to Phase 2

Detection Time: 60+ seconds
Example:
  T+0s: Database connection fails → breaker opens
  T+30s: Retry attempt fails → breaker remains OPEN
  T+60s: Database still unavailable → rollback triggered
```

### 6. Prediction Service Failure

```
Trigger: prediction_breaker.state == OPEN for >60 seconds

What Happens:
1. Prediction service tracks failure count
2. If OPEN for 60+ seconds:
   - ML service confirmed unavailable
   - Fallback to rules-based prediction
   - If persistent >2 min: trigger rollback

Detection Time: 120+ seconds
Example:
  T+0s: Prediction service timeout → breaker opens
  T+60s: Recovery still failing → continue open
  T+120s: Still failing after 2 min → rollback triggered
```

---

## Automatic Rollback Sequence

### What Happens Automatically (No Action Needed)

When any trigger condition is met, the system executes this sequence:

```
[1] DETECTION (< 10 seconds)
    └─ Trigger condition detected
    └─ Rollback manager activated
    └─ Alert: "Phase 3 Rollback Triggered" → CRITICAL
    └─ Alert sent to on-call engineer

[2] FEATURE FLAG DISABLE (< 500ms)
    └─ UPDATE system_config SET PHASE_3_ACTIVE = 'false'
    └─ All new requests route to Phase 2 logic
    └─ Immediate traffic stop for Phase 3 operations

[3] MONITORING DAEMON STOP (< 5 seconds)
    └─ Kill monitoring daemon process
    └─ Stop checkpoint collection
    └─ Archive current checkpoint data

[4] DATABASE BACKUP RESTORE (5-30 seconds)
    └─ Restore from latest backup: data/backups/phase3_start_*.sqlite
    └─ Transaction rollback to pre-Phase3 state
    └─ Verify integrity after restore

[5] WEBSOCKET EVENT BROADCAST (< 1 second)
    └─ Send phase3:rollback_triggered event
    └─ Dashboard updates to show rollback status
    └─ Real-time notification to monitoring team

[6] LOG ARCHIVAL (< 5 seconds)
    └─ Archive Phase 3 checkpoint data
    └─ Save rollback decision and timestamp
    └─ Preserve logs for post-mortem analysis

[7] ALERT NOTIFICATION (< 2 seconds)
    └─ Send CRITICAL alert to on-call
    └─ Send notification email to Phase 3 Owner
    └─ Update incident tracking system

TOTAL TIME TO STABLE STATE: < 60 seconds
```

### Verification of Automatic Rollback

After automatic rollback triggers, verify it succeeded:

```bash
# 1. Verify feature flag disabled
sqlite3 data/db.sqlite3 "SELECT value FROM system_config WHERE key='PHASE_3_ACTIVE'"
# Should return: false

# 2. Verify monitoring daemon stopped
ps aux | grep monitoring_daemon | grep -v grep
# Should return: (empty - process killed)

# 3. Verify traffic reverted to Phase 2
grep "PHASE_3_ACTIVE" logs/backend.log | tail -2
# Should show: "PHASE_3_ACTIVE = false"

# 4. Verify backup restore completed
grep -i "restore" logs/backend.log | tail -3
# Should show: "Database restore from backup completed"

# 5. Verify checkpoint stopped
ls -la logs/phase3/checkpoint_HORA_*.json | tail -1
# Latest checkpoint should match time of rollback trigger

# 6. Check rollback log entry
grep "rollback.*triggered" logs/rollback.log | tail -1
# Should show timestamp, trigger reason, status
```

---

## Manual Rollback (Emergency)

If immediate rollback is needed before automatic trigger:

### Kill-Switch Endpoint

```bash
# Command
curl -X POST http://localhost:8000/api/admin/phase3/deactivate \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Emergency manual deactivation"}'

# Response (success)
{
  "status": "success",
  "message": "Phase 3 deactivated",
  "timestamp": "2026-10-06T22:35:00Z",
  "feature_flag": "PHASE_3_ACTIVE = false",
  "traffic_status": "Reverted to Phase 2",
  "backup_restore": "In progress",
  "time_to_stable": "< 60 seconds"
}

# Response (error)
{
  "status": "error",
  "message": "Not authorized or invalid token",
  "code": 401
}
```

### Getting Admin Token

If you need to authorize the kill-switch request:

```bash
# Get token from admin credentials
export ADMIN_TOKEN=$(python3 -c "
from backend.auth import get_admin_token
token = get_admin_token()
print(token)
")

# Or use environment variable (if pre-configured)
export ADMIN_TOKEN="your-admin-token-here"

# Test token validity
curl -X GET http://localhost:8000/api/admin/health \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"
```

### Manual Rollback Procedure

If API endpoint unavailable, perform manual rollback:

```bash
# Step 1: Disable feature flag directly
python3 -c "
import sqlite3
from backend.config import DATABASE_PATH

db = sqlite3.connect(DATABASE_PATH)
cursor = db.cursor()
cursor.execute(\"UPDATE system_config SET value='false' WHERE key='PHASE_3_ACTIVE'\")
db.commit()
db.close()
print('✓ PHASE_3_ACTIVE = false')
"

# Step 2: Kill monitoring daemon
pkill -f "monitoring_daemon"
echo "✓ Monitoring daemon stopped"

# Step 3: Restore database from backup
python3 -c "
import sqlite3
from pathlib import Path
from backend.config import DATABASE_PATH, BACKUP_DIR

# Find latest backup
backup_dir = Path(BACKUP_DIR)
backups = sorted(backup_dir.glob('*.sqlite'), key=lambda p: p.stat().st_mtime, reverse=True)

if not backups:
    print('✗ No backup found!')
    exit(1)

backup_file = backups[0]
print(f'Restoring from: {backup_file.name}')

# Perform restore
source = sqlite3.connect(str(backup_file))
dest = sqlite3.connect(DATABASE_PATH)
source.backup(dest)
dest.close()
source.close()

print(f'✓ Database restored from backup')
"

# Step 4: Broadcast rollback event
python3 -c "
from backend.websocket_manager import get_connection_manager
ws = get_connection_manager()
ws.broadcast({
    'event_type': 'phase3:rollback',
    'reason': 'Manual emergency deactivation',
    'status': 'rollback_complete'
})
print('✓ Rollback event broadcast')
"

# Step 5: Log rollback
echo "Manual rollback executed at $(date)" >> logs/rollback_log.txt
echo "✓ Rollback logged"

# Step 6: Verify rollback complete
echo "✓ Phase 3 Rollback Complete"
echo "  - Feature flag disabled"
echo "  - Monitoring stopped"
echo "  - Database restored"
echo "  - Traffic reverted to Phase 2"
```

---

## Post-Rollback Procedures

### Immediate Actions (First 5 Minutes)

**1. Verify System Stability**

```bash
# Check Phase 2 is handling traffic
curl -s http://localhost:8000/health | python3 -m json.tool

# Verify no errors in logs
tail -20 logs/backend.log | grep -i error

# Check database connectivity
python3 -c "
import sqlite3
db = sqlite3.connect('data/db.sqlite3')
cursor = db.cursor()
cursor.execute('SELECT COUNT(*) FROM ab_tests')
print(f'✓ Database: {cursor.fetchone()[0]} tests found')
db.close()
"
```

**2. Notify Stakeholders**

```bash
# Email to Phase 3 Owner
echo "Phase 3 Rollback triggered at $(date)
Reason: Check logs
Status: Reverted to Phase 2
Action: Awaiting investigation" | \
  mail -s "ALERT: Phase 3 Rollback" felipe@enbuenamesa.com

# Slack notification (if configured)
# Send message to #phase3-alerts channel
```

**3. Review Trigger Reason**

```bash
# Check what triggered the rollback
grep -i "trigger.*reason" logs/rollback.log | tail -1

# Example outputs:
# - insufficient_healthy_metrics (metric_count=3)
# - latency_spike (latency_ms=245)
# - error_rate_spike (error_rate_pct=0.65)
# - critical_alert (alert: database_unavailable)
# - database_connection_loss
# - prediction_service_unavailable
# - manual_deactivation (reason: emergency)
```

### Investigation Phase (Next 30 Minutes)

**1. Collect Diagnostic Data**

```bash
# Gather Phase 3 checkpoint data
mkdir -p analysis/
cp -r logs/phase3/ analysis/phase3_checkpoints/

# Collect system logs
tail -500 logs/backend.log > analysis/backend_errors.log

# Check database integrity after restore
python3 -c "
import sqlite3
db = sqlite3.connect('data/db.sqlite3')
cursor = db.cursor()
result = cursor.execute('PRAGMA integrity_check').fetchone()
print(f'Database Integrity: {result[0]}')
db.close()
"

# Export last few checkpoint files for analysis
python3 -c "
import json
import glob

checkpoints = sorted(glob.glob('logs/phase3/checkpoint_*.json'))
print('Checkpoints collected during Phase 3:')

for cp_file in checkpoints[-5:]:  # Last 5 checkpoints
    with open(cp_file) as f:
        cp = json.load(f)
    print(f'  HORA {cp[\"hora\"]}: {cp[\"status\"]} → {cp[\"decision\"]}')
"
```

**2. Analyze Root Cause**

```bash
# Review rollback trigger details
cat logs/rollback.log | tail -20

# Check metric trends leading to rollback
python3 -c "
import json
import glob

print('Metrics trend analysis (last 3 checkpoints):')
print()

checkpoints = sorted(glob.glob('logs/phase3/checkpoint_*.json'))

for cp_file in checkpoints[-3:]:
    with open(cp_file) as f:
        cp = json.load(f)
    
    print(f'HORA {cp[\"hora\"]}:')
    for metric, value in cp['metrics'].items():
        target = cp['thresholds'][metric]['target']
        healthy = cp['thresholds'][metric]['healthy']
        status = '✓' if healthy else '✗'
        print(f'  {status} {metric}: {value:.4f} (target: {target})')
    print()
"

# Check if metric was consistently failing
python3 -c "
import json
import glob

metrics_history = {}
checkpoints = sorted(glob.glob('logs/phase3/checkpoint_*.json'))

for cp_file in checkpoints:
    with open(cp_file) as f:
        cp = json.load(f)
    
    for metric, health in cp['thresholds'].items():
        if metric not in metrics_history:
            metrics_history[metric] = []
        metrics_history[metric].append({
            'hora': cp['hora'],
            'healthy': health['healthy']
        })

print('Metric Health Timeline:')
for metric, history in metrics_history.items():
    failures = sum(1 for h in history if not h['healthy'])
    print(f'{metric}: {failures} failures out of {len(history)} checkpoints')
"
```

**3. Determine If Phase 3 Can Retry**

```bash
# Criteria for retry:
# 1. Root cause identified and fixed
# 2. System is stable (Phase 2 running normally)
# 3. Enough time to complete new Phase 3 window
# 4. Stakeholder approval obtained

echo "Phase 3 Retry Readiness Checklist:"
echo "[ ] Root cause identified"
echo "[ ] Root cause has been fixed"
echo "[ ] Phase 2 metrics all GREEN for 1+ hour"
echo "[ ] All circuit breakers in CLOSED state"
echo "[ ] No active alerts or warnings"
echo "[ ] Backup created from current state"
echo "[ ] Team approval obtained"
echo "[ ] New 24-hour window scheduled"
"
```

### Archive & Documentation (Next Hour)

**1. Create Post-Mortem Report**

```bash
python3 -c "
import json
from datetime import datetime
from pathlib import Path

post_mortem = {
    'timestamp': datetime.utcnow().isoformat(),
    'event': 'phase3_rollback_analysis',
    'summary': {
        'trigger': 'insufficient_healthy_metrics',  # Replace with actual
        'time_in_phase3': '2 hours 15 minutes',
        'last_healthy_checkpoint': 50,
        'rollback_checkpoint': 52,
        'time_to_rollback': '< 60 seconds'
    },
    'metrics_at_rollback': {
        'ml_accuracy': 0.75,  # Example
        'error_rate': 0.00095,
        'websocket_latency': 105,
        'predictions_hour': 38,
        'personalization_active': 120,
        'active_tests': 6
    },
    'root_cause_analysis': {
        'primary_cause': 'ML model accuracy degradation',
        'contributing_factors': ['Insufficient training data', 'Data drift'],
        'evidence': 'Checkpoint 50 showed early accuracy decline (76.2%)'
    },
    'corrective_actions': [
        'Retrain ML model with latest data',
        'Increase accuracy threshold validation',
        'Add data drift monitoring'
    ],
    'recommendations': [
        'Resume Phase 3 after model retraining',
        'Reduce checkpoint interval to 1.5 hours',
        'Add early warning alert at 77% accuracy'
    ]
}

# Save post-mortem
report_path = Path('analysis/phase3_postmortem.json')
report_path.parent.mkdir(parents=True, exist_ok=True)

with open(report_path, 'w') as f:
    json.dump(post_mortem, f, indent=2)

print(f'✓ Post-mortem saved: {report_path}')
"
```

**2. Archive Phase 3 Data**

```bash
# Create timestamped archive
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_DIR="archives/phase3_rollback_${TIMESTAMP}"

mkdir -p "${ARCHIVE_DIR}"

# Copy all relevant files
cp -r logs/phase3/ "${ARCHIVE_DIR}/"
cp logs/rollback_log.txt "${ARCHIVE_DIR}/"
cp logs/phase3_activation.json "${ARCHIVE_DIR}/"
cp analysis/phase3_postmortem.json "${ARCHIVE_DIR}/"

# Create summary
cat > "${ARCHIVE_DIR}/README.md" << 'EOF'
# Phase 3 Rollback Analysis

Rollback occurred during Phase 3 execution.

## Files in this archive:
- `phase3/`: All checkpoint JSON files
- `rollback_log.txt`: Rollback trigger log
- `phase3_activation.json`: Original activation details
- `phase3_postmortem.json`: Root cause analysis

## Next Steps:
1. Review postmortem
2. Implement corrective actions
3. Schedule Phase 3 retry
EOF

echo "✓ Phase 3 data archived to: ${ARCHIVE_DIR}"
```

**3. Cleanup Phase 3 Database State**

```bash
# Remove Phase 3 feature flag (optional - keep for retry)
# sqlite3 data/db.sqlite3 "DELETE FROM system_config WHERE key='PHASE_3_ACTIVE'"

# Reset personalization_variants to Phase 1 (10%)
sqlite3 data/db.sqlite3 "UPDATE personalization_variants SET rollout_phase=1 WHERE rollout_phase > 1"

# Verify Phase 2 is restored
python3 -c "
import sqlite3
db = sqlite3.connect('data/db.sqlite3')
cursor = db.cursor()

# Check personalization state
cursor.execute('SELECT COUNT(*) as cnt FROM personalization_variants WHERE rollout_phase=1')
phase1_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) as cnt FROM personalization_variants WHERE rollout_phase > 1')
phase_other_count = cursor.fetchone()[0]

print(f'✓ Phase 1 records: {phase1_count}')
print(f'✓ Phase 2+ records: {phase_other_count} (should be 0)')

db.close()
"
```

---

## Recovery & Retry Planning

### Criteria for Phase 3 Retry

Before attempting Phase 3 again, verify:

```bash
# 1. Root cause fixed
echo "Root cause: [documented issue]"
echo "Fix applied: [describe fix]"
echo "Testing completed: [yes/no]"

# 2. System stability
for i in {1..6}; do
    python3 -c "
    from backend.rollback_manager import RollbackManager
    rm = RollbackManager()
    # Get current metrics
    "
done
echo "✓ 6 consecutive metric collections OK"

# 3. Phase 2 baseline restored
python3 -c "
from backend.monitoring import get_health_checker
health = get_health_checker().evaluate_health()
print(f'Phase 2 Status: {health.get(\"overall_status\")}')
for metric, data in health.get('metrics', {}).items():
    print(f'  {metric}: {data.get(\"status\")}')
"

# 4. Time available for full 24-hour window
echo "Current time: $(date)"
echo "Phase 3 restart time: [time to restart]"
echo "Days until time window: [calculate]"
```

### Scheduling Phase 3 Retry

```bash
# Plan retry execution
python3 -c "
import json
from datetime import datetime, timedelta

retry_plan = {
    'rollback_analysis_complete': True,
    'fixes_implemented': True,
    'team_approval_obtained': True,
    'scheduled_restart': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
    'estimated_completion': (datetime.utcnow() + timedelta(hours=48)).isoformat(),
    'risk_level': 'LOW',
    'notes': 'Second attempt with fix for ML accuracy degradation'
}

with open('phase3_retry_schedule.json', 'w') as f:
    json.dump(retry_plan, f, indent=2)

print('✓ Phase 3 retry scheduled')
print(f\"  Restart: {retry_plan['scheduled_restart']}\")
print(f\"  Completion: {retry_plan['estimated_completion']}\")
"

# Notify team
echo "Phase 3 retry scheduled for $(date)" | \
  mail -s "Phase 3 Retry Scheduled" felipe@enbuenamesa.com
```

---

## Rollback Summary

### What Was Lost

After rollback:
- ❌ All Phase 3 test results from current execution
- ❌ Rollout data (who received winning variant)
- ❌ Checkpoints after rollback trigger
- ✅ Phase 2 baseline data (restored)
- ✅ All tests and configurations (preserved)
- ✅ Historical A/B test data (intact)

### What Was Preserved

- ✅ Database integrity (restored from backup)
- ✅ Test configurations (unchanged)
- ✅ Participant data (restored to pre-Phase3)
- ✅ A/B test history (intact for analysis)
- ✅ Logs for investigation (archived)

### Time to Restore Phase 2 Functionality

```
T+0s:   Rollback triggered
T+10s:  Feature flag disabled, new traffic → Phase 2
T+20s:  Database restore complete
T+50s:  WebSocket events restored
T+60s:  Full system stable, Phase 2 operational
```

**Users Experience:**
- Immediate: New sessions route to Phase 2
- 10-30 seconds: Existing sessions handled by Phase 2
- <1 minute: Complete restoration to Phase 2 baseline

---

## Escalation & Communication

### Incident Notification Template

```
INCIDENT: Phase 3 Rollback

Severity: HIGH
Timestamp: [ISO timestamp]
Duration: [how long Phase 3 was active]

Trigger: [insufficient_metrics / latency_spike / error_spike / critical_alert]
Root Cause: [brief description]

System Impact:
- Phase 3 deactivated
- All traffic reverted to Phase 2
- Database restored from backup

Actions Taken:
- Rollback completed in <60 seconds
- Archive created
- Post-mortem analysis initiated

Status: STABLE - Phase 2 running normally
Next Step: Root cause investigation and retry planning

Contact: Felipe (felipe@enbuenamesa.com)
```

---

**Document Version:** 1.0  
**Last Updated:** October 6, 2026  
**Status:** Production Ready
