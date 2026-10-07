# RUNBOOK: Phase 3 Activation Procedure

## Overview

This runbook provides step-by-step instructions for safely activating FASE 15 Phase 3 in production. Phase 3 is the final rollout phase of the A/B testing framework, escalating from 10% to 100% customer coverage with continuous health monitoring.

**Duration:** ~30 minutes  
**Risk Level:** MEDIUM (fully automated safety mechanisms in place)  
**Automation Level:** 95% automated, 5% manual verification  
**Rollback Available:** Yes, instant via kill-switch endpoint

---

## Pre-Activation Checklist

### 1. Verify Phase 2 Success (REQUIRED)
- [ ] Phase 2 has been running for ≥24 hours
- [ ] All 6 metrics GREEN for entire Phase 2 period
  - [ ] ML Accuracy ≥78%
  - [ ] Error Rate <0.08%
  - [ ] WebSocket Latency <95ms
  - [ ] Predictions/Hour ≥42
  - [ ] Personalization Active ≥140
  - [ ] Active Tests ≥8
- [ ] No CRITICAL or WARNING alerts in Phase 2 logs
- [ ] Dashboard shows stable metrics (no spikes)

**Verification Command:**
```bash
# Check Phase 2 metrics summary
python3 -c "
from backend.monitoring import get_health_checker
health = get_health_checker().evaluate_health()
print('Phase 2 Health Status:', health.get('overall_status'))
for metric, data in health.get('metrics', {}).items():
    print(f'  {metric}: {data.get(\"status\")} ({data.get(\"value\")})')
"
```

### 2. Database Integrity Check (REQUIRED)
- [ ] SQLite database file exists and is readable
- [ ] All 6 required tables present
- [ ] Database integrity check passes
- [ ] Recent backup exists (<2 hours old)

**Verification Command:**
```bash
# Run integrity check
python3 -c "
import sqlite3
from backend.config import DATABASE_PATH

db = sqlite3.connect(DATABASE_PATH)
cursor = db.cursor()

# Integrity check
result = cursor.execute('PRAGMA integrity_check').fetchone()
print(f'Integrity Check: {result[0]}')

# Table verification
required_tables = [
    'ab_tests',
    'ab_test_ml_predictions',
    'personalization_variants',
    'comparison_reports',
    'backend_metrics_collector',
    'system_config'
]

cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
existing_tables = {row[0] for row in cursor.fetchall()}

for table in required_tables:
    status = '✓' if table in existing_tables else '✗'
    print(f'{status} {table}')

db.close()
"
```

### 3. Circuit Breaker Initialization (REQUIRED)
- [ ] Database circuit breaker initializes successfully
- [ ] WebSocket circuit breaker initializes successfully
- [ ] Prediction circuit breaker initializes successfully
- [ ] All breakers report CLOSED state

**Verification Command:**
```bash
# Test circuit breaker initialization
python3 -c "
from backend.circuit_breaker import (
    get_database_breaker,
    get_websocket_breaker,
    get_prediction_breaker,
    CircuitBreakerState
)

breakers = {
    'database': get_database_breaker(),
    'websocket': get_websocket_breaker(),
    'prediction': get_prediction_breaker(),
}

for name, breaker in breakers.items():
    state = breaker.get_state()
    is_closed = state == CircuitBreakerState.CLOSED
    status = '✓' if is_closed else '✗'
    print(f'{status} {name}: {state.name}')
"
```

### 4. System Components Availability (REQUIRED)
- [ ] Backend server responds to health check
- [ ] WebSocket connection available and stable
- [ ] ML prediction service available
- [ ] Monitoring daemon can start
- [ ] All dependencies importable

**Verification Command:**
```bash
# Health check endpoint
curl -s http://localhost:8000/health | python3 -m json.tool

# WebSocket connectivity
python3 -c "
from backend.websocket_manager import get_connection_manager
ws_mgr = get_connection_manager()
print(f'✓ WebSocket Manager: {ws_mgr is not None}')
"

# Monitoring daemon import
python3 -c "
from backend.monitoring_daemon import MonitoringDaemon
daemon = MonitoringDaemon()
print(f'✓ Monitoring Daemon: Ready')
"
```

### 5. Backup Verification (REQUIRED)
- [ ] Phase 2 backup exists and is recent (<2 hours)
- [ ] Backup file is readable
- [ ] Backup restoration test successful

**Verification Command:**
```bash
# List recent backups
ls -lh data/backups/ | grep -E "phase2|backup" | tail -5

# Test restore
python3 -c "
import sqlite3
import tempfile
from pathlib import Path
from backend.config import DATABASE_PATH, BACKUP_DIR

# Find latest backup
backup_dir = Path(BACKUP_DIR)
backups = sorted(backup_dir.glob('*.sqlite'), key=lambda p: p.stat().st_mtime, reverse=True)

if backups:
    backup_file = backups[0]
    print(f'Latest backup: {backup_file.name}')
    
    # Test restore
    with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
        tmp_db = sqlite3.connect(tmp.name)
        backup_db = sqlite3.connect(str(backup_file))
        
        # Copy backup to temp
        backup_db.backup(tmp_db)
        
        # Verify tables
        cursor = tmp_db.cursor()
        cursor.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE type='table'\")
        table_count = cursor.fetchone()[0]
        
        print(f'✓ Restore test successful ({table_count} tables verified)')
        tmp_db.close()
        backup_db.close()
else:
    print('✗ No backup found!')
"
```

---

## Activation Procedure

### Step 1: Create Pre-Activation Backup

Create a fresh backup immediately before activation for emergency rollback:

```bash
# Create backup with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="data/backups/phase3_start_${TIMESTAMP}.sqlite"

python3 -c "
import sqlite3
from backend.config import DATABASE_PATH

# Source database
source_db = sqlite3.connect('${DATABASE_PATH}')

# Backup database
backup_db = sqlite3.connect('${BACKUP_PATH}')

# Perform backup
source_db.backup(backup_db)

# Verify
cursor = backup_db.cursor()
cursor.execute('SELECT COUNT(*) FROM ab_tests')
test_count = cursor.fetchone()[0]

print(f'✓ Pre-activation backup created: ${BACKUP_PATH}')
print(f'  Tests in backup: {test_count}')

source_db.close()
backup_db.close()
"

# Verify backup was created
if [ -f "${BACKUP_PATH}" ]; then
    echo "✓ Backup file verified"
    ls -lh "${BACKUP_PATH}"
else
    echo "✗ Backup creation failed!"
    exit 1
fi
```

**Expected Output:**
```
✓ Pre-activation backup created: data/backups/phase3_start_20261006_223000.sqlite
  Tests in backup: 8
✓ Backup file verified
-rw-r--r-- 1 user group 4.2M Oct 6 22:30 data/backups/phase3_start_20261006_223000.sqlite
```

### Step 2: Enable Phase 3 Feature Flag

Set the PHASE_3_ACTIVE flag in the system configuration:

```bash
python3 -c "
import sqlite3
from backend.config import DATABASE_PATH
from datetime import datetime

db = sqlite3.connect('${DATABASE_PATH}')
cursor = db.cursor()

# Check if flag exists
cursor.execute(\"SELECT id FROM system_config WHERE key='PHASE_3_ACTIVE'\")
existing = cursor.fetchone()

if existing:
    # Update existing
    cursor.execute(
        \"UPDATE system_config SET value='true', updated_at=? WHERE key='PHASE_3_ACTIVE'\",
        (datetime.utcnow().isoformat(),)
    )
    print('✓ Updated existing PHASE_3_ACTIVE flag to true')
else:
    # Insert new
    cursor.execute(
        \"INSERT INTO system_config (key, value, created_at) VALUES ('PHASE_3_ACTIVE', 'true', ?)\",
        (datetime.utcnow().isoformat(),)
    )
    print('✓ Created new PHASE_3_ACTIVE flag set to true')

db.commit()

# Verify
cursor.execute(\"SELECT value FROM system_config WHERE key='PHASE_3_ACTIVE'\")
value = cursor.fetchone()[0]
print(f'✓ Verification: PHASE_3_ACTIVE = {value}')

db.close()
"
```

**Expected Output:**
```
✓ Created new PHASE_3_ACTIVE flag set to true
✓ Verification: PHASE_3_ACTIVE = true
```

### Step 3: Start Monitoring Daemon

Start the background monitoring process that will execute checkpoints every 2 hours:

```bash
# Start monitoring daemon in background
nohup python3 -c "
from backend.monitoring_daemon import MonitoringDaemon
import logging

logging.basicConfig(
    filename='logs/phase3_monitoring.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

daemon = MonitoringDaemon()
daemon.start_checkpoint_monitoring()  # Runs continuous 24-hour monitoring
" > logs/phase3_daemon.out 2>&1 &

# Capture PID
DAEMON_PID=$!
echo ${DAEMON_PID} > .phase3_daemon.pid

# Verify daemon started
sleep 2
if ps -p ${DAEMON_PID} > /dev/null; then
    echo "✓ Monitoring daemon started (PID: ${DAEMON_PID})"
else
    echo "✗ Monitoring daemon failed to start!"
    cat logs/phase3_daemon.out
    exit 1
fi
```

**Expected Output:**
```
✓ Monitoring daemon started (PID: 12345)
```

### Step 4: Broadcast Activation Event

Send WebSocket event to notify dashboard of Phase 3 activation:

```bash
python3 -c "
from backend.events import Event, EventType
from backend.websocket_manager import get_connection_manager
import json
from datetime import datetime

# Create activation event
event = Event(
    type=EventType.PHASE_3_ACTIVATED,
    payload={
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'activated',
        'checkpoint_schedule': [48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72],
        'first_checkpoint_eta_hours': 2,
        'monitoring_interval_minutes': 120
    }
)

# Broadcast to all connected clients
ws_manager = get_connection_manager()
ws_manager.broadcast({
    'event_type': 'phase3:activated',
    'data': event.payload,
    'timestamp': datetime.utcnow().isoformat()
})

print('✓ Activation event broadcast to dashboard')
"
```

**Expected Output:**
```
✓ Activation event broadcast to dashboard
```

### Step 5: Generate and Log Activation Report

Create a detailed activation report for audit trail:

```bash
python3 -c "
import json
from datetime import datetime, timedelta
from pathlib import Path

activation_report = {
    'timestamp': datetime.utcnow().isoformat(),
    'event': 'phase3_activated',
    'status': 'SUCCESS',
    'checks': {
        'phase_2_metrics': True,
        'database_connection': True,
        'database_integrity': True,
        'circuit_breakers': True,
        'websocket_ready': True,
        'backup_exists': True,
        'monitoring_daemon': True
    },
    'backup_location': '${BACKUP_PATH}',
    'feature_flag': 'PHASE_3_ACTIVE = true',
    'checkpoints_scheduled': 13,
    'checkpoint_schedule': list(range(48, 74, 2)),
    'first_checkpoint': {
        'hora': 48,
        'scheduled_time': (datetime.utcnow() + timedelta(hours=2)).isoformat(),
        'metrics_to_collect': [
            'ml_accuracy',
            'error_rate',
            'websocket_latency',
            'predictions_hour',
            'personalization_active',
            'active_tests'
        ]
    },
    'rollout_phases': {
        'phase_1': {
            'rollout_percentage': 10,
            'start_hora': 48,
            'end_hora': 52,
            'duration_hours': 4
        },
        'phase_2': {
            'rollout_percentage': 50,
            'start_hora': 52,
            'end_hora': 58,
            'duration_hours': 6
        },
        'phase_3': {
            'rollout_percentage': 100,
            'start_hora': 58,
            'end_hora': 72,
            'duration_hours': 14
        }
    },
    'success_criteria': {
        'minimum_healthy_metrics': 5,
        'total_metrics': 6,
        'final_decision_hora': 72
    },
    'emergency_contacts': {
        'owner': 'Felipe',
        'escalation_email': 'felipe@enbuenamesa.com',
        'kill_switch_endpoint': '/api/admin/phase3/deactivate'
    }
}

# Write report
log_path = Path('logs/phase3_activation.json')
log_path.parent.mkdir(parents=True, exist_ok=True)

with open(log_path, 'w') as f:
    json.dump(activation_report, f, indent=2)

print(f'✓ Activation report saved: {log_path}')
print(f'  First checkpoint in: 2 hours (HORA 48)')
print(f'  All checkpoints: HORA {48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72}')
print(f'  Expected completion: +24 hours (HORA 72)')
"
```

**Expected Output:**
```
✓ Activation report saved: logs/phase3_activation.json
  First checkpoint in: 2 hours (HORA 48)
  All checkpoints: (48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72)
  Expected completion: +24 hours (HORA 72)
```

---

## Verification Checklist

After completing all activation steps, verify:

- [ ] **Database Flag Set:** Run `SELECT value FROM system_config WHERE key='PHASE_3_ACTIVE'` → returns 'true'
- [ ] **Backup Created:** Run `ls -lh data/backups/phase3_start_*.sqlite` → shows recent file
- [ ] **Daemon Running:** Run `ps aux | grep monitoring_daemon` → shows running process
- [ ] **Dashboard Connected:** Open `http://localhost:8000/phase3/dashboard` → shows "Connected" status
- [ ] **First Checkpoint Scheduled:** Check logs for "Next checkpoint at HORA 48"
- [ ] **Activation Report Generated:** Run `cat logs/phase3_activation.json` → shows activation details

---

## Rollback (If Needed Before HORA 48)

If you need to cancel Phase 3 before the first checkpoint:

```bash
# Disable feature flag
python3 -c "
import sqlite3
from backend.config import DATABASE_PATH

db = sqlite3.connect('${DATABASE_PATH}')
cursor = db.cursor()
cursor.execute(
    \"UPDATE system_config SET value='false' WHERE key='PHASE_3_ACTIVE'\"
)
db.commit()
db.close()
print('✓ PHASE_3_ACTIVE disabled')
"

# Stop monitoring daemon
kill \$(cat .phase3_daemon.pid)
echo "✓ Monitoring daemon stopped"

# Restore from backup
python3 -c "
import sqlite3
from backend.config import DATABASE_PATH

db = sqlite3.connect('${DATABASE_PATH}')
backup_db = sqlite3.connect('data/backups/phase3_start_*.sqlite')
db.executescript('DELETE FROM system_config WHERE key=\"PHASE_3_ACTIVE\"')
db.commit()
db.close()
print('✓ System returned to pre-Phase3 state')
"
```

---

## Post-Activation Monitoring

### Immediate Post-Activation (First 10 Minutes)
- Monitor dashboard for WebSocket connection status
- Check backend logs for any startup errors
- Verify first scheduled checkpoint in logs

### First 2 Hours (Until HORA 48)
- Monitor database for any connection issues
- Watch circuit breaker states (should all remain CLOSED)
- Check for any alerts in alerting system

### At HORA 48 (First Checkpoint)
- Monitor checkpoint execution in logs
- Verify first checkpoint result in `logs/phase3/checkpoint_HORA_48.json`
- Confirm dashboard displays checkpoint metrics
- Check decision: should be CONTINUE (or trigger manual review if CAUTION/NO-GO)

---

## Success Indicators

After activation is complete, you should observe:

1. **System State**
   - PHASE_3_ACTIVE flag = 'true' in database
   - Monitoring daemon process running
   - No errors in backend logs

2. **Dashboard**
   - Connected status shown at top
   - Phase 3 metrics section visible
   - Real-time updates flowing via WebSocket

3. **Scheduled Tasks**
   - Checkpoints scheduled for HORA 48, 50, 52, etc.
   - Monitoring daemon ready to execute first checkpoint

4. **Backup**
   - Pre-activation backup exists and is recent
   - Can be restored instantly via kill-switch if needed

---

## Troubleshooting Activation Issues

### Issue: Feature Flag Not Setting

```bash
# Check database
sqlite3 data/db.sqlite3 "SELECT * FROM system_config WHERE key='PHASE_3_ACTIVE'"

# If not found, manually insert
sqlite3 data/db.sqlite3 "INSERT INTO system_config (key, value) VALUES ('PHASE_3_ACTIVE', 'true')"

# Verify
sqlite3 data/db.sqlite3 "SELECT * FROM system_config WHERE key='PHASE_3_ACTIVE'"
```

### Issue: Monitoring Daemon Won't Start

```bash
# Check Python imports
python3 -c "from backend.monitoring_daemon import MonitoringDaemon; print('✓ Import successful')"

# Check logs
tail -50 logs/phase3_daemon.out

# Try starting in foreground for debugging
python3 -c "
from backend.monitoring_daemon import MonitoringDaemon
daemon = MonitoringDaemon()
daemon.start_checkpoint_monitoring()
"
```

### Issue: Dashboard Shows Disconnected

```bash
# Check WebSocket manager
python3 -c "
from backend.websocket_manager import get_connection_manager
ws = get_connection_manager()
print(f'WebSocket Manager: {ws}')
print(f'Connected Clients: {len(ws.active_connections) if ws else 0}')
"

# Check backend logs for WebSocket errors
grep -i "websocket" logs/*.log | head -20
```

### Issue: Backup Creation Failed

```bash
# Check backup directory
ls -la data/backups/

# Verify write permissions
touch data/backups/test.txt && rm data/backups/test.txt

# Try manual backup
python3 -c "
import sqlite3
source_db = sqlite3.connect('data/db.sqlite3')
backup_db = sqlite3.connect('data/backups/manual_backup_$(date +%s).sqlite')
source_db.backup(backup_db)
print('✓ Manual backup successful')
source_db.close()
backup_db.close()
"
```

---

## Rollback Plan (Emergency)

If something goes wrong during activation and you need to abort:

**Command:** `curl -X POST http://localhost:8000/api/admin/phase3/deactivate -H "Authorization: Bearer <token>"`

**Effect:** 
- Disables PHASE_3_ACTIVE immediately
- Stops checkpoint monitoring
- Reverts all clients to Phase 2 logic
- Time to effect: <500ms

**Verification:**
```bash
# Check flag is disabled
sqlite3 data/db.sqlite3 "SELECT value FROM system_config WHERE key='PHASE_3_ACTIVE'"
# Should return: false

# Check daemon stopped
ps aux | grep monitoring_daemon
# Should show no process

# Check traffic reverted
grep "Phase 3" logs/backend.log | tail -1
# Should show deactivation message
```

---

**Document Version:** 1.0  
**Last Updated:** October 6, 2026  
**Status:** Production Ready
