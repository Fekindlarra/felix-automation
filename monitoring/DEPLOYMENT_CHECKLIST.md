# Phase 3 Monitoring - Deployment Checklist

**Pre-Execution Checklist:** Complete all items before HORA 48 activation

---

## ✅ Infrastructure Setup (24 hours before Phase 3)

- [ ] Prometheus installed and running
- [ ] Grafana installed and running  
- [ ] Alertmanager installed and running
- [ ] All services accessible from network
- [ ] Disk space verified (10GB minimum for Prometheus metrics)
- [ ] Network connectivity tested between services
- [ ] SSL certificates installed (if using HTTPS)

## ✅ Configuration Deployment

- [ ] `prometheus_rules_phase3.yaml` deployed to `/etc/prometheus/rules/`
- [ ] `grafana_dashboard_phase3.json` imported into Grafana
- [ ] `alertmanager_config_phase3.yaml` deployed to `/etc/alertmanager/`
- [ ] `anomaly_detection_config.yaml` loaded
- [ ] `sla_tracking_config.yaml` configured
- [ ] Environment variables set:
  - [ ] `SLACK_WEBHOOK_URL`
  - [ ] `PAGERDUTY_SERVICE_KEY`
  - [ ] `PAGERDUTY_EMERGENCY_KEY`
  - [ ] `SMTP_SERVER`, `SMTP_USER`, `SMTP_PASSWORD`

## ✅ Data Source Configuration

- [ ] Prometheus data source added to Grafana
- [ ] Data source health check passing
- [ ] Test query returns data: `up{job="phase3_api"}`
- [ ] Metric scrape configured for all Phase 3 services:
  - [ ] Phase 3 API endpoint (`localhost:8000/metrics/phase3`)
  - [ ] Database metrics endpoint
  - [ ] Prediction service endpoint
  - [ ] WebSocket service endpoint

## ✅ Dashboard Verification

- [ ] Dashboard loads without errors
- [ ] All 14 panels rendering
- [ ] Sample data visible in panels
- [ ] Time range selector working
- [ ] Panel edit mode functional
- [ ] Export functionality working

## ✅ Alert Rules Verification

- [ ] All 30+ alert rules loaded in Prometheus
- [ ] Test alert can be triggered manually
- [ ] Alert threshold values correct
- [ ] Alert severity levels appropriate
- [ ] No alert rule syntax errors in logs

## ✅ Notification Channel Testing

### Slack
- [ ] Webhook URL configured and working
- [ ] Test message sent successfully
- [ ] Channel permissions verified
- [ ] Message formatting correct
- [ ] Buttons/actions working

### PagerDuty
- [ ] Service key configured
- [ ] Test incident created and resolved
- [ ] Escalation policy verified
- [ ] On-call rotation assigned
- [ ] Email notifications enabled

### Email
- [ ] SMTP server accessible
- [ ] Test email sent to felipe@enbuenamesa.com
- [ ] HTML formatting verified
- [ ] Links in email working

## ✅ Anomaly Detection Setup

- [ ] Baseline metrics established (1+ hour of data)
- [ ] All 6 anomaly detectors enabled
- [ ] Z-score thresholds validated
- [ ] Multi-metric anomaly rules configured
- [ ] Test anomaly detection with synthetic data

## ✅ SLA Tracking Configuration

- [ ] Availability SLA query configured (99.5% target)
- [ ] Performance SLA query configured (<95ms)
- [ ] Reliability SLA query configured (<0.08% errors)
- [ ] Functionality SLA query configured (6 KPIs)
- [ ] SLA compliance dashboard panels added

## ✅ Logging & Audit

- [ ] Alert logs collecting to `logs/alerts/`
- [ ] Metric export logs collecting
- [ ] Prometheus retention set to 24+ hours
- [ ] Log rotation configured
- [ ] Audit trail enabled for Grafana changes

## ✅ Documentation

- [ ] Team briefed on dashboard locations
- [ ] Runbooks reviewed and accessible
- [ ] Emergency contacts documented
- [ ] Escalation procedures understood
- [ ] Access credentials shared securely

## ✅ Performance & Stress Testing

- [ ] Dashboard loads in <2 seconds
- [ ] Query latency <1 second (p95)
- [ ] Alert evaluation time <30 seconds
- [ ] WebSocket connection latency <100ms
- [ ] CPU usage <30% during normal operation
- [ ] Memory usage <2GB for Prometheus

## ✅ Backup & Disaster Recovery

- [ ] Prometheus configuration backed up
- [ ] Grafana dashboard JSON backed up
- [ ] Alertmanager config backed up
- [ ] Recovery procedure documented
- [ ] Restore time <15 minutes

---

## Phase 3 Activation (HORA 48)

### T-30 Minutes

- [ ] Dashboard open and monitoring
- [ ] All services showing green status
- [ ] No pending alerts
- [ ] SLA baseline established
- [ ] On-call team notified

### T-5 Minutes

- [ ] Metrics flowing normally
- [ ] Alert rules evaluated (no false positives)
- [ ] Anomaly detection baseline ready
- [ ] All notification channels tested
- [ ] Phase 3 activation command ready

### T+0 Minutes (HORA 48 - Activation)

- [ ] Phase 3 activated successfully
- [ ] Initial metrics recording
- [ ] Dashboard showing live data
- [ ] First alert threshold checks executed
- [ ] WebSocket event stream active

### T+30 Minutes

- [ ] 30 minutes of metric data collected
- [ ] Anomaly detection learning from baseline
- [ ] No spurious alerts firing
- [ ] Dashboard responsive and updated
- [ ] SLA tracking initialized

### T+2 Hours (HORA 50 - First Checkpoint)

- [ ] Checkpoint metrics collected
- [ ] Decision calculated (CONTINUE/CAUTION/NO-GO)
- [ ] Health score displayed
- [ ] First hourly report generated
- [ ] Team briefed on status

---

## Continuous Monitoring (HORA 48-72)

### Every 30 Minutes
- [ ] Check dashboard health score
- [ ] Review active alerts
- [ ] Monitor anomaly score
- [ ] Verify metric freshness

### Every 2 Hours (At Each Checkpoint)
- [ ] Review checkpoint decision
- [ ] Assess health metrics
- [ ] Check for anomalies
- [ ] Generate hourly report
- [ ] Brief team on status

### Escalation Triggers
- [ ] If health score <5/6 → Investigate
- [ ] If critical alert → Page on-call
- [ ] If rollback triggered → Emergency response
- [ ] If SLA missed → Incident escalation

---

## Post-Execution (HORA 72)

### Final Assessment
- [ ] All 24 hours of metrics collected
- [ ] Final health score calculated
- [ ] SLA compliance report generated
- [ ] Incident analysis complete
- [ ] Business impact calculated

### Reporting
- [ ] Executive summary sent to leadership
- [ ] Detailed metrics report generated
- [ ] Dashboard archived for audit
- [ ] Lessons learned documented
- [ ] Improvements planned for Phase 4

### Cleanup
- [ ] Prometheus metrics exported and archived
- [ ] Alert logs archived
- [ ] Dashboard permissions reset
- [ ] Alertmanager silenced (if not rolling over)
- [ ] Post-mortem scheduled if needed

---

## Sign-Off

**Monitoring Setup Owner:** _____________________

**Date Completed:** _____________________

**All Items Complete:** ☐ YES ☐ NO

**Approved for Phase 3 Activation:** ☐ YES ☐ NO

**Notes/Issues:**
```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```

---

## Emergency Contact Tree

**Phase 3 Owner:** Felipe  
📧 felipe@enbuenamesa.com  
📱 On-call rotation via PagerDuty

**On-Call Engineer:**  
📧 oncall@enbuenamesa.com  
📱 PagerDuty alert

**SRE Team Lead:**  
📧 sre-lead@enbuenamesa.com

**Database Admin:**  
📧 dba@enbuenamesa.com

**ML Team Lead:**  
📧 ml-lead@enbuenamesa.com

---

**Prepared:** October 6, 2026  
**Version:** 1.0  
**Status:** Ready for Phase 3 Deployment
