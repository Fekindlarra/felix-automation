# 📘 FASE 14 Deployment Runbook

**For:** Production Deployment & Operations  
**Version:** 1.0  
**Last Updated:** 2026-10-05  
**Owner:** DevOps/Platform Team  

---

## 🎯 QUICK REFERENCE

### Common Commands

```bash
# Check system health
curl https://api.domain.com/api/monitoring/health

# Check dashboard metrics
curl https://api.domain.com/api/monitoring/dashboard

# View recent logs
kubectl logs -f deployment/fase14-api --tail=100

# Scale WebSocket servers
kubectl scale deployment fase14-websocket --replicas=5

# Check active WebSocket connections
curl https://api.domain.com/api/monitoring/metrics/websocket_connections

# Perform graceful shutdown
kubectl set deployment fase14-api min-ready-seconds=30
kubectl rollout pause deployment fase14-api
```

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### 1. Code Verification (30 minutes before)

```bash
# Pull latest code
git fetch origin
git checkout release/fase14-v1.0.0

# Verify version tag
git describe --tags

# Run quick test suite
pytest tests/unit/ -x -q
# Expected: All tests pass

# Build Docker image
docker build -t fase14:release-1.0.0 .
# Expected: Build succeeds, no warnings
```

### 2. Database Verification (1 hour before)

```bash
# Backup current database
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > backup-$(date +%Y%m%d-%H%M%S).sql

# Test migration on backup
python scripts/migrate_db.py --environment=staging --backup=backup-*.sql
# Expected: Migration succeeds, all tables present

# Verify backup size
du -h backup-*.sql
# Expected: Size reasonable (< 10GB for normal database)
```

### 3. Environment Verification (30 minutes before)

```bash
# Check environment variables set
env | grep FASE14

# Verify SSL certificates
echo | openssl s_client -connect api.domain.com:443 | grep -A 5 "subject="
# Expected: Certificate valid for >30 days

# Check database connectivity
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"
# Expected: Returns 1

# Check Redis connectivity
redis-cli -h $REDIS_HOST PING
# Expected: Returns PONG

# Check API server health (current version)
curl https://api.domain.com/api/health
# Expected: Returns 200 OK with health data
```

### 4. Alert Configuration (15 minutes before)

```bash
# Verify Slack integration
curl -X POST $SLACK_WEBHOOK -d '{"text":"Deployment test message"}'
# Expected: Message appears in Slack

# Verify PagerDuty integration
curl https://api.pagerduty.com/incidents \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2"
# Expected: Returns list of incidents

# Test alert creation
curl https://api.domain.com/api/monitoring/test-alert -X POST
# Expected: Alert appears in monitoring dashboard
```

---

## 🚀 DEPLOYMENT PROCEDURE

### Phase 1: Pre-Deployment (30 minutes)

```bash
# Step 1: Notify team
echo "🚀 FASE 14 v1.0.0 deployment starting..."
# Post to #deployments Slack channel

# Step 2: Set maintenance mode (optional)
kubectl create configmap deployment-in-progress --from-literal=status=deploying

# Step 3: Scale WebSocket servers up
kubectl scale deployment fase14-websocket --replicas=5
# Wait: ~2 minutes for new pods to be ready
kubectl get pods -l app=fase14-websocket

# Step 4: Drain connections gracefully
# Tell existing connections to migrate to new servers
kubectl exec -it $POD_NAME -- curl localhost:8000/api/shutdown/graceful

# Step 5: Backup current state
kubectl get all > backups/state-$(date +%Y%m%d-%H%M%S).yaml
```

### Phase 2: Database Migration (5-10 minutes)

```bash
# Step 1: Create backup
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > backup-deployment.sql

# Step 2: Run migration
python scripts/migrate_db.py --environment=production --backup=backup-deployment.sql
# Watch output for:
# - ✓ All migrations applied
# - ✓ Schema verification successful
# - ✓ Data integrity checks passed

# Step 3: Verify migration
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt"
# Expected: All expected tables present

# Step 4: Warm up connections
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM clients"
# Expected: Counts return quickly
```

### Phase 3: Deploy New Code (10-15 minutes)

```bash
# Step 1: Push Docker image to registry
docker tag fase14:release-1.0.0 registry.domain.com/fase14:latest
docker push registry.domain.com/fase14:latest
# Wait: ~5 minutes for push to complete

# Step 2: Update Kubernetes deployment
kubectl set image deployment/fase14-api \
  fase14=registry.domain.com/fase14:latest \
  --record

# Step 3: Monitor rollout
kubectl rollout status deployment/fase14-api
# Expected: "deployment "fase14-api" successfully rolled out"
# Timeout: ~5 minutes

# Step 4: Verify new pods are running
kubectl get pods -l app=fase14-api
# Expected: All pods in READY 1/1 status, RESTARTS = 0
```

### Phase 4: Health Verification (5-10 minutes)

```bash
# Step 1: API health check
curl https://api.domain.com/api/health
# Expected: Returns {"status": "healthy"}

# Step 2: WebSocket connectivity
wscat -c wss://api.domain.com/ws
# Expected: Connection established (can see connected message)

# Step 3: Monitoring dashboard
curl https://api.domain.com/api/monitoring/dashboard
# Expected: Returns metrics with all checks "healthy"

# Step 4: Smoke test prediction flow
curl -X POST https://api.domain.com/api/predictions/test \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -d '{"client_id": "test-001"}'
# Expected: Returns 200 with prediction data

# Step 5: Smoke test A/B test dashboard
curl https://api.domain.com/frontend/ab_testing_dashboard.html
# Expected: Returns 200 OK (HTML page loads)

# Step 6: Verify logs have no errors
kubectl logs -f deployment/fase14-api --tail=50 | grep ERROR
# Expected: No ERROR lines (or only INFO/DEBUG)
```

### Phase 5: Post-Deployment (5 minutes)

```bash
# Step 1: Clear maintenance mode
kubectl delete configmap deployment-in-progress

# Step 2: Scale WebSocket servers to normal
kubectl scale deployment fase14-websocket --replicas=3

# Step 3: Update deployment tracking
git tag -a v14.0.0-deployed-prod -m "Deployed to production $(date)"
git push origin v14.0.0-deployed-prod

# Step 4: Announce deployment complete
echo "✅ FASE 14 v1.0.0 successfully deployed to production"
# Post to #deployments Slack channel with:
# - Deployment time
# - Number of commits
# - Key features deployed
```

---

## ⏱️ ROLLBACK PROCEDURE

**Use this if:** Deployment causes critical errors (error rate > 5%, latency > 500ms, or WebSocket failures)

```bash
# ⚠️ DECISION POINT: Only execute if absolutely necessary
# Review: Health metrics, error logs, monitoring dashboard

# Step 1: Alert team immediately
echo "🚨 ROLLBACK INITIATED - FASE 14 v1.0.0"
# Post critical alert to #incidents Slack channel

# Step 2: Stop new deployment
kubectl rollout undo deployment/fase14-api
# This reverts to previous image version

# Step 3: Monitor rollback
kubectl rollout status deployment/fase14-api
# Expected: "deployment "fase14-api" successfully rolled out"

# Step 4: Verify previous version working
curl https://api.domain.com/api/health
# Expected: Returns {"status": "healthy"}

# Step 5: Check if database rollback needed
# Usually NOT needed - new version should be backward compatible
# Only if migration broke compatibility:
# psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f backup-deployment.sql

# Step 6: Verify all systems operational
# Re-run smoke tests from Phase 4

# Step 7: Post-mortem
# Document:
# - What failed
# - When it was detected
# - When rollback was initiated
# - Time to recovery
# - Root cause analysis needed
```

**Expected rollback time:** 5-10 minutes

---

## 🔍 MONITORING AFTER DEPLOYMENT

### First 1 Hour (Critical Monitoring)

Check every 5 minutes:

```bash
# Check 1: Error rate
curl https://api.domain.com/api/monitoring/dashboard | jq '.health.metrics.error_rate'
# Target: < 1%

# Check 2: WebSocket latency
curl https://api.domain.com/api/monitoring/dashboard | jq '.websocket_metrics.current_latency'
# Target: < 100ms

# Check 3: Active connections
curl https://api.domain.com/api/monitoring/dashboard | jq '.websocket_metrics.active_connections'
# Target: Normal operational level

# Check 4: Logs for errors
kubectl logs -f deployment/fase14-api | grep -i error

# Check 5: Alert count
curl https://api.domain.com/api/monitoring/health | jq '.alerts | length'
# Target: 0 active alerts
```

### First 24 Hours (Continuous Monitoring)

Check every 30 minutes:

```bash
# Generate metrics report
curl https://api.domain.com/api/monitoring/dashboard > metrics-$(date +%H:%M).json

# Check for trends
# - Error rate increasing? (indicates cascading failures)
# - Latency increasing? (indicates resource exhaustion)
# - Connection failures? (indicates network issues)

# Monitor database performance
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Monitor API performance by endpoint
kubectl exec -it $POD_NAME -- curl localhost:8000/api/monitoring/endpoints
```

### Alert Thresholds (Trigger Actions)

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error Rate | > 2% for 5 min | Alert team |
| Error Rate | > 5% for 5 min | Page on-call |
| Latency p95 | > 200ms for 10 min | Investigate scaling |
| Connections failed | > 10% for 5 min | Check network |
| Cache hit rate | < 70% for 10 min | Review caching |
| Offline users | > 15% for 10 min | Check infrastructure |

---

## 🐛 TROUBLESHOOTING

### Issue: "Connection refused" when accessing API

```bash
# Diagnosis
kubectl get pods -l app=fase14-api
kubectl describe pod $POD_NAME

# Solutions
# 1. Check if pod is running
kubectl get pods -l app=fase14-api | grep -v Running

# 2. Check if service is accessible
kubectl get svc fase14-api
kubectl port-forward svc/fase14-api 8000:8000
curl localhost:8000/api/health

# 3. Check logs
kubectl logs $POD_NAME
# Look for startup errors

# 4. Restart pod
kubectl delete pod $POD_NAME
# Pod will auto-restart
```

### Issue: "WebSocket connection timeout"

```bash
# Diagnosis
kubectl logs -f deployment/fase14-websocket | tail -100

# Solutions
# 1. Check if WebSocket service is running
kubectl get pods -l app=fase14-websocket

# 2. Check connection limits
ulimit -n
# Should be > 65536

# 3. Scale WebSocket servers
kubectl scale deployment fase14-websocket --replicas=5

# 4. Check network connectivity
kubectl exec -it $POD_NAME -- ping $BACKEND_IP
```

### Issue: "Database connection pool exhausted"

```bash
# Diagnosis
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT count(*) FROM pg_stat_activity;"
# Should be < 20 connections normally

# Solutions
# 1. Increase connection pool size
# Edit: backend/config.yaml
# db:
#   pool_size: 20
#   max_overflow: 10

# 2. Kill idle connections
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE datname = current_database() AND usename = 'app_user' AND state = 'idle' AND query_start < now() - INTERVAL '10 minutes';
"

# 3. Restart API pods to reset connections
kubectl rollout restart deployment/fase14-api
```

### Issue: "Cache hit rate < 70%"

```bash
# Diagnosis
curl https://api.domain.com/api/monitoring/metrics/cache_hit_rate

# Solutions
# 1. Check service worker status in browser console
navigator.serviceWorker.getRegistrations()

# 2. Clear old caches
# In browser console:
caches.keys().then(names => Promise.all(names.map(n => caches.delete(n))))

# 3. Force service worker update
navigator.serviceWorker.getRegistration().then(r => r.update())

# 4. Check what's not being cached
# Review service_worker.js caching strategy
# Increase MAX_CACHE_SIZE if needed
```

---

## 📞 ESCALATION PROCEDURES

### Level 1: Application Team (Response time: 15 minutes)

**Who:** Developers, QA engineers  
**On-call rotation:** Check PagerDuty schedule  

**Responsibilities:**
- Monitor dashboards first 24 hours
- Check application logs
- Validate smoke tests
- Respond to monitoring alerts

### Level 2: DevOps Team (Response time: 30 minutes)

**Who:** DevOps engineers, platform team  
**On-call rotation:** Check PagerDuty schedule  

**Responsibilities:**
- Infrastructure health
- Database issues
- Kubernetes/orchestration
- Network connectivity

### Level 3: Engineering Lead (Response time: 1 hour)

**Who:** Tech lead, engineering manager  
**Responsibilities:**
- Major incident coordination
- Decision to rollback
- Stakeholder communication
- Root cause analysis

---

## 📚 USEFUL COMMANDS

```bash
# View deployment history
kubectl rollout history deployment/fase14-api

# Show specific deployment revision
kubectl rollout history deployment/fase14-api --revision=5

# Get real-time metrics
kubectl top nodes
kubectl top pods -l app=fase14-api

# SSH into running container
kubectl exec -it $POD_NAME -- /bin/bash

# View environment variables
kubectl exec $POD_NAME -- env | grep FASE14

# Check resource usage
kubectl describe node
kubectl describe pod $POD_NAME | grep -A 5 "Limits\|Requests"

# Stream logs from multiple pods
kubectl logs -f -l app=fase14-api --all-containers=true

# Get events sorted by time
kubectl get events --sort-by='.lastTimestamp'
```

---

## 🎓 TRAINING & CERTIFICATION

### Required Training

- [ ] Kubernetes basics (kubectl commands, deployments, services)
- [ ] FASE 14 architecture overview
- [ ] Monitoring dashboard walkthrough
- [ ] Incident response procedures
- [ ] Rollback procedure (hands-on practice)

### Certification

**New team members must:**
1. Read this runbook completely
2. Perform a supervised deployment in staging
3. Pass incident response simulation
4. Be approved by tech lead before production access

---

## 📞 EMERGENCY CONTACTS

During critical incidents:

- **Tech Lead:** [Name] - [Phone]
- **DevOps Lead:** [Name] - [Phone]  
- **On-Call Rotation:** See PagerDuty schedule
- **Slack:** #incidents (critical), #deployments (planned)

---

**Last Revised:** 2026-10-05  
**Next Review:** 2026-11-05  
**Approved By:** [Engineering Lead]
