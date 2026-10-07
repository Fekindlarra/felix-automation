# FASE 15 Phase 3 - Advanced Monitoring & Alerting Setup Guide

**Status:** Production Ready  
**Last Updated:** October 6, 2026  
**Audience:** DevOps Engineers, SREs, Operations Team

---

## Overview

This guide covers the complete Advanced Monitoring & Alerting System for FASE 15 Phase 3 production execution. The system provides real-time health tracking, automated alerting, anomaly detection, and SLA compliance monitoring across all 6 KPIs.

### Components

1. **Prometheus Rules** - Alert rules for 30+ conditions
2. **Grafana Dashboard** - Real-time visualization with 14 panels
3. **Alertmanager** - Alert routing, escalation, and notifications
4. **Anomaly Detection** - Statistical and ML-based anomaly detection
5. **SLA Tracking** - Compliance monitoring against SLAs

### Quick Stats

- **30+ Alert Rules** covering all 6 KPIs, circuit breakers, rollback triggers
- **14 Dashboard Panels** with real-time metrics, health status, trends, alerts
- **6 Anomaly Detectors** per metric (Z-score, IQR, Isolation Forest, etc.)
- **5 SLA Categories** (Availability, Performance, Reliability, Functionality, Business)
- **Multi-Channel Notifications** (Slack, PagerDuty, Email)
- **<5 Second** Dashboard refresh rate
- **99.5% Target Uptime** for Phase 3 execution

---

## 1. Prerequisites

### Required Services

```bash
# Prometheus (metrics scraping and alerting)
docker pull prom/prometheus:latest
docker run -d --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus_rules_phase3.yaml:/etc/prometheus/rules.yaml \
  prom/prometheus --config.file=/etc/prometheus/prometheus.yml

# Grafana (dashboard and visualization)
docker pull grafana/grafana:latest
docker run -d --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana

# Alertmanager (alert routing and notification)
docker pull prom/alertmanager:latest
docker run -d --name alertmanager \
  -p 9093:9093 \
  -v $(pwd)/monitoring/alertmanager_config_phase3.yaml:/etc/alertmanager/config.yml \
  prom/alertmanager --config.file=/etc/alertmanager/config.yml
```

### Environment Variables Required

```bash
# Slack integration
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# PagerDuty integration
export PAGERDUTY_SERVICE_KEY="pkey-1234567890abcdef"
export PAGERDUTY_EMERGENCY_KEY="pkey-emergency-key"

# Email configuration
export SMTP_SERVER="smtp.gmail.com"
export SMTP_USER="alerts@enbuenamesa.com"
export SMTP_PASSWORD="app-specific-password"
```

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 30s
  evaluation_interval: 30s

rule_files:
  - 'monitoring/prometheus_rules_phase3.yaml'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

scrape_configs:
  # Phase 3 API metrics
  - job_name: 'phase3_api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/phase3'

  # Phase 3 Database metrics
  - job_name: 'phase3_database'
    static_configs:
      - targets: ['localhost:5432']

  # Phase 3 Prediction Service metrics
  - job_name: 'phase3_predictions'
    static_configs:
      - targets: ['localhost:8001']

  # Phase 3 WebSocket metrics
  - job_name: 'phase3_websocket'
    static_configs:
      - targets: ['localhost:8002']
```

---

## 2. Alert Rules Configuration

### File: `prometheus_rules_phase3.yaml`

**Coverage:** 30+ alert rules organized in groups

#### 1. KPI Alerts (24 rules)
- ML Accuracy: Target below, Critical drop, Anomaly detection
- Error Rate: Elevated, Spike, Trend degradation
- WebSocket Latency: Elevated, Spike, Anomaly
- Predictions/Hour: Below target, Critical, Service unavailable
- Personalization: Adoption drop, Critical, Service issue
- Active Tests: Below target, Critical

#### 2. Circuit Breaker Alerts (3 rules)
- Database Circuit Breaker (OPEN state)
- WebSocket Circuit Breaker (OPEN state)
- Prediction Service Circuit Breaker (OPEN state)

#### 3. Checkpoint Alerts (3 rules)
- Checkpoint CONTINUE decision
- Checkpoint CAUTION decision (5/6 metrics healthy)
- Checkpoint NO-GO decision (automatic rollback trigger)

#### 4. Infrastructure Alerts (2 rules)
- Metrics collector down
- Checkpoint execution delayed (>5 minutes)

#### 5. Recording Rules (7 rules)
- 5-minute average for all 6 metrics
- Health status for each metric
- Overall health score (0-6)

### Severity Levels

| Severity | Response Time | Escalation | Use Case |
|----------|---------------|-----------|----------|
| Critical | Immediate (0s) | PagerDuty + Email + Slack | Rollback triggers, health failures, service down |
| Warning | 5-10 minutes | Slack + Email | Threshold misses, anomalies, degradation |
| Info | No escalation | Slack only | Checkpoint decisions, phase advancement |

### Custom Thresholds

To modify alert thresholds, edit the metric expressions in `prometheus_rules_phase3.yaml`:

```yaml
# Example: Change ML accuracy alert threshold from 0.78 to 0.80
- alert: Phase3MLAccuracyBelowTarget
  expr: fase15_phase3_ml_accuracy{phase="3"} < 0.80  # Changed from 0.78
```

---

## 3. Grafana Dashboard

### File: `grafana_dashboard_phase3.json`

**Access:** `http://localhost:3000/d/fase15-phase3-monitoring`

### Dashboard Panels (14 total)

#### Health Status Panels (2)
1. **Health Metrics Status (Pie Chart)**
   - Shows all 6 KPIs and their health status
   - 6 green slices = all healthy
   - Red/orange slices = problematic metrics

2. **Overall Health Score (Gauge)**
   - Displays 0-6 healthy metrics
   - Green: 6/6, Yellow: 5/6, Red: <5/6
   - Auto-escalates alert if score drops below 5

#### KPI Trend Panels (6)
3. **ML Accuracy Trend** (Target: ≥78%)
   - 5-minute average line chart
   - Target threshold line
   - Mean, Max, Min, Last values in legend

4. **Error Rate Trend** (Target: <0.08%)
   - Inverted scale (lower is better)
   - Warning zone (>0.08%), Critical zone (>0.5%)

5. **WebSocket Latency Trend** (Target: <95ms)
   - Red zone (>200ms = automatic rollback)
   - Yellow zone (95-200ms)

6. **Predictions/Hour Trend** (Target: ≥42)
7. **Personalization Active Trend** (Target: ≥140)
8. **Active Tests Trend** (Target: ≥8)

#### Infrastructure Panels (3)
9. **Current Metrics Table**
   - Real-time values for all 6 KPIs
   - Sortable by metric, value, or status

10. **Circuit Breaker Status**
    - Green (CLOSED): Normal operation
    - Red (OPEN): Not accepting requests
    - Yellow (HALF_OPEN): Testing recovery

11. **Health Score Over Time**
    - Historical view of health score across 24h
    - Shows when score dropped below 5

#### Alert & Status Panels (3)
12. **Active Alerts Count**
    - Number of critical and warning alerts
    - Color-coded severity

13. **Service Health Status**
    - Shows up/down for: API, Database, Predictions, WebSocket

14. **Active Phase 3 Alerts Table**
    - Detailed alert list with timestamps
    - Sortable and searchable

### Dashboard Features

**Auto-Refresh:** 5 seconds (configurable)  
**Time Range:** Last 2 hours (24h available)  
**Theme:** Dark mode (optimized for 24/7 monitoring)

### Importing Dashboard

```bash
# 1. Log into Grafana
# http://localhost:3000 (admin/admin)

# 2. Click "+" → "Import"

# 3. Upload JSON file:
# monitoring/grafana_dashboard_phase3.json

# 4. Select Prometheus data source

# 5. Click "Import"
```

### Dashboard Customization

**Add Panel:**
1. Click "Add panel" → "Add a new panel"
2. Select Prometheus data source
3. Enter PromQL query
4. Configure visualization
5. Save dashboard

**Edit Thresholds:**
1. Select panel
2. Click "Edit"
3. Go to "Thresholds" tab
4. Modify threshold values
5. Click "Save"

---

## 4. Alertmanager Configuration

### File: `alertmanager_config_phase3.yaml`

**Access:** `http://localhost:9093`

### Alert Routing Logic

```
Root Route
├── Critical Phase 3 (instant) → Slack, PagerDuty, Email
├── Rollback Emergency (instant) → Slack, PagerDuty, Email (urgent)
├── Checkpoint Decisions → Slack, Email
├── Phase 3 Warnings (30s batch) → Slack, Email
└── Monitoring Alerts → Slack only
```

### Notification Channels

#### 1. Slack
- **Channel:** `#phase3-critical` (critical alerts)
- **Channel:** `#phase3-warnings` (warnings)
- **Format:** Alert name, component, value, description
- **Actions:** View Dashboard, Kill Switch, Acknowledge

#### 2. PagerDuty
- **Service:** Phase 3 Production
- **Urgency:** Critical for severity=critical
- **Auto-resolve:** When alert resolves
- **Escalation:** After 5 minutes without acknowledgment

#### 3. Email
- **To:** `felipe@enbuenamesa.com`
- **Format:** HTML with full details and links
- **Digest:** Batched every 30 seconds

### Testing Alerts

```bash
# Test Slack webhook
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Phase 3 Alert Test"}'

# Send test alert to Alertmanager
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "phase": "3"
    },
    "annotations": {
      "summary": "Test alert"
    }
  }]'
```

### Inhibition Rules

Suppresses non-critical alerts when critical alerts are firing:

```
If rollback triggered → Suppress all other Phase 3 warnings
If health fails → Suppress individual metric warnings
If checkpoint NO-GO → Suppress circuit breaker warnings
If critical alert → Suppress related warnings
```

---

## 5. Anomaly Detection

### File: `anomaly_detection_config.yaml`

**Methods:** Z-score, IQR, Isolation Forest, trend analysis

### Per-Metric Anomaly Detectors

#### ML Accuracy (3 detectors)
- **Z-score:** 3-sigma detection (99.7% confidence)
- **IQR:** Interquartile range outlier detection
- **Isolation Forest:** ML-based anomaly detection

#### Error Rate (3 detectors)
- **Percentage Change:** >50% increase from baseline
- **Z-score:** 2.5-sigma (98% confidence)
- **Absolute Threshold:** >0.5% spike detection

#### WebSocket Latency (3 detectors)
- **Spike Detection:** >200ms for 2+ consecutive checks
- **Rate of Change:** >20ms/minute increase
- **EWMA:** Deviation from exponential moving average

#### Predictions/Hour (2 detectors)
- **Throughput Drop:** >30% decrease
- **Z-score:** Statistical outlier

#### Personalization (2 detectors)
- **Adoption Drop:** >25% decrease
- **Rate of Change:** >5 instances/minute drop

#### Active Tests (1 detector)
- **Test Drop:** >20% decrease from baseline

### Multi-Metric Anomalies

**Cascading Failure Pattern:**
- Triggered when 3+ metrics show simultaneous anomalies
- Indicates system-wide degradation
- Auto-escalates to CRITICAL severity

**Partial Degradation Pattern:**
- Triggered when 3 of 6 metrics are anomalous
- Indicates component issues
- Severity: WARNING

**Latency-Driven Errors Pattern:**
- Correlated spike in latency AND error rate
- Indicates network/performance issue
- Action: Investigate network

**Resource Exhaustion Pattern:**
- Both throughput and adoption dropping
- Indicates resource limits hit
- Action: Check resource usage

### Anomaly Score Dashboard

```
Anomaly Score (0-10):
0-2: Normal
2-4: Abnormal but acceptable
4-6: Elevated anomaly level
6-8: High anomaly level (alert soon)
8-10: Critical anomaly (alert immediately)
```

### Customizing Anomaly Detection

Edit threshold in `anomaly_detection_config.yaml`:

```yaml
# Change Z-score threshold from 3 to 2.5
detectors:
  - name: "zscore"
    threshold: 2.5  # More sensitive
```

---

## 6. SLA Tracking

### File: `sla_tracking_config.yaml`

**Tracks:** Availability, Performance, Reliability, Functionality, Business metrics

### SLA Targets

| SLA | Target | Window | Allowed Miss |
|-----|--------|--------|--------------|
| Availability | 99.5% | 24h | 7.2 minutes |
| Latency (p95) | <95ms | 24h | 1% of requests |
| Error Rate | <0.08% | 1m | 0.1% of requests |
| ML Accuracy | ≥78% | 24h | 2 of 13 checkpoints |
| Predictions | ≥42/hour | 24h | 10% of hours |
| Rollbacks | 0 | 24h | 0 |

### SLA Compliance Queries

```promql
# Availability percentage
(1 - downtime_minutes / 1440) * 100

# Latency SLA compliance (% meeting <95ms target)
(requests_under_95ms / total_requests) * 100

# Reliability SLA compliance (% meeting <0.08% error target)
(1 - error_rate_pct / 0.08) * 100
```

### SLA Reporting

**Report Schedule:**
- Hourly: During Phase 3 execution (HORA 48-72)
- 6-hourly: Cumulative summaries
- Final: At HORA 72 completion

**Report Contents:**
1. Executive summary (PASS/CAUTION/FAIL)
2. Metric-by-metric compliance
3. Incident response times
4. Business impact calculation
5. Recommendations for Phase 4

**Report Template:**
```
# FASE 15 Phase 3 - SLA Compliance Report

## Key Metrics
- Availability: 99.8% ✅ (Target: 99.5%)
- Error Rate: 0.047% ✅ (Target: <0.08%)
- Latency (p95): 42ms ✅ (Target: <95ms)
- ML Accuracy Checkpoints: 13/13 ✅ (Target: 11/13)
- Rollbacks: 0 ✅ (Target: 0)

## Overall Compliance
✅ **PASS** - 100% SLA compliance achieved
```

---

## 7. Operational Procedures

### Starting Phase 3 Monitoring

```bash
# 1. Start Prometheus
docker start prometheus

# 2. Start Alertmanager
docker start alertmanager

# 3. Start Grafana
docker start grafana

# 4. Verify all services running
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:9093/-/healthy  # Alertmanager
curl http://localhost:3000/api/health  # Grafana

# 5. Open Grafana dashboard
open http://localhost:3000/d/fase15-phase3-monitoring
```

### Monitoring During Phase 3 Execution

**Every 30 seconds:**
- Prometheus evaluates alert rules
- Updated metrics sent to Grafana
- Anomalies detected and analyzed

**Every hour (at checkpoint):**
- Checkpoint status evaluated
- Health score calculated
- SLA compliance checked
- Dashboard updated

**Every 2 hours:**
- Checkpoint data saved to logs
- Decision made (CONTINUE/CAUTION/NO-GO)
- Events broadcast to WebSocket

**Continuously:**
- Real-time WebSocket events
- Latency measurements
- Error rate tracking
- ML prediction accuracy monitoring

### Dashboard Monitoring Checklist

| Time | Action | Target Value | Alert Threshold |
|------|--------|--------------|-----------------|
| T-5m | Verify all services up | Green | Any red |
| T+0m | Phase 3 activated | 6/6 healthy | <6/6 |
| T+30m | First metrics flowing | Baseline established | Gaps in data |
| T+2h | First checkpoint | CONTINUE or CAUTION | NO-GO |
| T+4h | Phase 1→2 transition | 50% rollout | Delayed transition |
| T+6h | Stability check | All green | Any yellow/red |
| T+10h | Phase 2→3 transition | 100% rollout | Delayed transition |
| T+12h | Midpoint assessment | 6/6 healthy | <5/6 |
| T+20h | Final phase check | 6/6 healthy | Any degradation |
| T+24h | Final checkpoint | SUCCESS/CAUTION/FAIL | Final decision |

### Emergency Procedures

**If Critical Alert Fires:**
1. Check Grafana dashboard
2. Verify alert in Alertmanager
3. Examine metrics for cause
4. Check Phase 3 logs
5. Escalate to on-call if needed

**If Rollback Triggered:**
1. Immediate: Verify rollback execution
2. Within 1 minute: Team notification
3. Within 5 minutes: Start incident investigation
4. Within 15 minutes: Post-mortem kickoff
5. Within 24 hours: Complete post-mortem

**If Dashboard Down:**
```bash
# Restart Grafana
docker restart grafana

# Access Alertmanager directly
http://localhost:9093

# Check Prometheus directly
curl http://localhost:9090/api/v1/query?query=fase15_phase3_health_score
```

---

## 8. Troubleshooting

### Alerts Not Firing

**Issue:** Alert rules defined but no alerts triggering

**Diagnosis:**
```bash
# 1. Check Prometheus is scraping metrics
curl http://localhost:9090/api/v1/targets

# 2. Check alert rule is loaded
curl http://localhost:9090/api/v1/rules

# 3. Verify PromQL query manually
curl 'http://localhost:9090/api/v1/query?query=fase15_phase3_ml_accuracy'
```

**Solution:**
- Verify metrics are being exported by Phase 3 services
- Check Prometheus scrape configuration
- Validate PromQL expressions in rules
- Restart Prometheus if rules updated

### Slack Notifications Not Arriving

**Issue:** Alerts fire but Slack channel has no messages

**Diagnosis:**
```bash
# 1. Verify Slack webhook URL
echo $SLACK_WEBHOOK_URL

# 2. Test webhook directly
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}'

# 3. Check Alertmanager logs
docker logs alertmanager
```

**Solution:**
- Verify webhook URL is correct and current
- Check Slack workspace permissions
- Test webhook with manual curl
- Verify Alertmanager config reloaded

### Grafana Dashboard Empty

**Issue:** Dashboard loads but panels show no data

**Diagnosis:**
```bash
# 1. Check Prometheus data source
# Grafana UI: Configuration → Data Sources → Prometheus → Test

# 2. Query Prometheus directly
curl http://localhost:9090/api/v1/query?query=fase15_phase3_ml_accuracy

# 3. Check panel PromQL
Click edit on empty panel → check query field
```

**Solution:**
- Wait 1-2 minutes for metrics to be collected
- Verify Prometheus data source connected
- Check panel PromQL expressions
- Reload dashboard (Ctrl+R)

### High CPU/Memory Usage

**Issue:** Prometheus or Grafana consuming excessive resources

**Solution:**
- Reduce Prometheus scrape frequency (30s → 60s)
- Disable unused recording rules
- Increase retention: `--storage.tsdb.retention.time=24h`
- Add more storage: `--storage.tsdb.path=/large-disk/prometheus`

---

## 9. Integration Points

### Metrics Export Endpoints

**Phase 3 API Endpoint:** `http://localhost:8000/metrics/phase3`
- Exports all 6 KPI metrics
- Format: Prometheus text format
- Updates every 30 seconds

**Expected Metrics:**
```
fase15_phase3_ml_accuracy{phase="3"} 0.837
fase15_phase3_error_rate{phase="3"} 0.00016
fase15_phase3_websocket_latency{phase="3"} 8
fase15_phase3_predictions_per_hour{phase="3"} 49
fase15_phase3_personalization_active{phase="3"} 152
fase15_phase3_active_tests{phase="3"} 10
```

### WebSocket Events

**Phase 3 Event Stream:** `ws://localhost:8000/ws/phase3`

**Consumed by:** Real-time dashboard, monitoring daemon

**Events:** 
- `phase3:checkpoint_completed` - Checkpoint finished
- `phase3:decision_made` - Decision (CONTINUE/CAUTION/NO-GO)
- `phase3:alert` - Alert triggered
- `phase3:rollback_triggered` - Rollback executed

### External Integrations

**Available integrations:**
- Slack: Alert notifications
- PagerDuty: On-call escalation
- Email: Executive summaries
- Datadog: Metrics forwarding (via Prometheus remote write)
- Custom webhooks: Call external APIs

---

## 10. References

**Configuration Files:**
- `prometheus_rules_phase3.yaml` - Alert rules (500 lines)
- `grafana_dashboard_phase3.json` - Dashboard (600 lines)
- `alertmanager_config_phase3.yaml` - Routing & notifications (300 lines)
- `anomaly_detection_config.yaml` - Anomaly detection (400 lines)
- `sla_tracking_config.yaml` - SLA compliance (500 lines)

**Related Documentation:**
- PHASE3_README.md - Architecture overview
- RUNBOOK_PHASE3_ACTIVATION.md - Activation procedures
- RUNBOOK_PHASE3_MONITORING.md - Operational monitoring
- RUNBOOK_PHASE3_ROLLBACK.md - Rollback procedures
- API_PHASE3_ENDPOINTS.md - API documentation

**Useful Links:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Alertmanager: http://localhost:9093
- Phase 3 API: http://localhost:8000/api/phase3

**Contacts:**
- Phase 3 Owner: Felipe (felipe@enbuenamesa.com)
- On-Call: Via PagerDuty escalation
- Emergency: Call on-call directly (see on-call schedule)

---

**Last Updated:** October 6, 2026  
**Version:** 1.0  
**Status:** Production Ready
