# FASE 14 Incident Response Playbook

**Document Type:** Emergency Response Procedures  
**Status:** ACTIVE (Post-Deployment)  
**Last Updated:** 2026-10-06 22:35 CLT  

---

## Quick Reference - Severity Levels

### CRITICAL (Page Immediately)
- Application down or unreachable
- Error rate > 1%
- Database unavailable
- Widespread customer impact
- **Response Time Target:** 5 minutes
- **Decision Time:** 15 minutes to escalate or resolve

### HIGH (Urgent Response)
- Major feature broken (e.g., WebSocket offline)
- Error rate 0.5-1%
- Partial customer impact
- Performance degraded >50%
- **Response Time Target:** 15 minutes
- **Decision Time:** 30 minutes to escalate

### MEDIUM (Standard Response)
- Minor feature issue
- Error rate 0.1-0.5%
- Limited customer impact
- Performance degraded 20-50%
- **Response Time Target:** 1 hour
- **Decision Time:** 2 hours to escalate

---

## Incident Response Flow

```
ALERT TRIGGERED
    ↓
IMMEDIATE ACTIONS (0-5 min)
├─ Acknowledge alert in PagerDuty
├─ Post to #fase-14-deployment Slack
├─ Gather current system metrics
├─ Determine severity level
└─ Page on-call engineer if CRITICAL
    ↓
INVESTIGATION (5-30 min)
├─ Check recent changes (git log)
├─ Review logs (application, database, WebSocket)
├─ Correlate with known issues
├─ Check if rollback needed
└─ Brief team on findings
    ↓
DECISION POINT
├─ IF RESOLVABLE → Execute fix
├─ IF REQUIRES ROLLBACK → Initiate rollback
└─ IF UNCLEAR → Escalate to engineering lead
    ↓
RESOLUTION (varies)
├─ Apply fix or rollback
├─ Verify metrics return to normal
├─ Confirm customer impact resolved
└─ Post-incident review scheduled
```

---

## Scenario Playbooks

### Scenario 1: WebSocket Connection Failures

**Symptoms:**
- WebSocket connections dropping
- Users seeing "connection lost" message
- Latency spiking or timeouts
- Mobile users particularly affected

**Investigation Steps (5-10 min):**
```bash
# 1. Check WebSocket server status
curl -s http://felix-api:8000/health | jq .websocket

# 2. Check connection count
kubectl logs -l app=felix-api -c felix-api | grep "active_connections"

# 3. Check for JWT auth errors
kubectl logs -l app=felix-api | grep "verify_jwt_token" | tail -20

# 4. Check pod resource usage
kubectl top pods -l app=felix-api

# 5. Check network connectivity
kubectl exec -it <pod-name> -- ping 8.8.8.8

# 6. Review recent changes
git log --oneline -20 | head -5
```

**Possible Root Causes:**
1. **JWT token verification failing** → Check JWT_SECRET environment variable
2. **Connection pool exhausted** → Check websocket.max_connections_per_server config
3. **Memory leak** → Check pod memory usage, restart if >90%
4. **Network issue** → Check pod logs for network errors
5. **Recent code change** → Check if deployment introduced auth regression

**Resolution Paths:**

**Path A: Quick Fix (JWT Secret Issue)**
```bash
# If JWT_SECRET was corrupted:
1. Verify JWT_SECRET in production secrets
2. Restart affected pods: kubectl rollout restart deployment/felix-api
3. Monitor WebSocket connections for recovery
4. Estimated time: 2-3 minutes
```

**Path B: Config Update (Connection Pool)**
```bash
# If connection pool too small:
1. Edit config.production.yaml
2. Increase max_connections_per_server: 2000 (from 1000)
3. Restart pods with rolling update
4. Monitor for recovery
5. Estimated time: 5 minutes
```

**Path C: Rollback (Deployment Issue)**
```bash
# If issue caused by v14.0.0 code:
kubectl rollout undo deployment/felix-api
kubectl rollout status deployment/felix-api -n production
# Verify service recovered
curl http://felix-api:8000/health
# Estimated time: 10-15 minutes
```

**Decision Matrix:**
```
Error Rate | Symptoms | Action
< 5% | Intermittent | Monitor, log issue
5-25% | Periodic drops | Apply Path A or B
> 25% | Frequent failures | Apply Path C (Rollback)
> 50% | Complete failure | Apply Path C immediately
```

**Post-Resolution:**
- [ ] Verify WebSocket connections stable for 5 minutes
- [ ] Check latency back to target <100ms
- [ ] Confirm users can connect
- [ ] Log incident details
- [ ] Schedule post-mortem if rollback occurred

---

### Scenario 2: Shopify API Rate Limiting Issue

**Symptoms:**
- Shopify sync failing intermittently
- 429 (Too Many Requests) errors in logs
- Orders not appearing in dashboard
- Webhook processing delays >30 seconds

**Investigation Steps (5-10 min):**
```bash
# 1. Check Shopify API error rate
kubectl logs -l app=felix-api | grep "shopify" | grep -i "429\|error" | wc -l

# 2. Check request rate
kubectl logs -l app=felix-api | grep "shopify_api" | tail -100 | \
  awk '{print $1}' | uniq -c | sort -rn

# 3. Check rate limiter state
kubectl logs -l app=felix-api | grep "rate_limiter" | tail -20

# 4. Check connection pool
kubectl logs -l app=felix-api | grep "connection_pool" | tail -20

# 5. Verify rate limit config
kubectl get configmap felix-config -o yaml | grep -A5 "shopify:"
```

**Possible Root Causes:**
1. **Rate limiter not working** → Bug in rate limiting logic
2. **Multiple pods hammering API** → Coordination issue between replicas
3. **Webhook storm** → Too many Shopify events coming in
4. **Connection pool leaking** → Connections not being returned
5. **Backend change introduced spike** → New code making extra API calls

**Resolution Paths:**

**Path A: Restart Rate Limiter Service**
```bash
# 1. Kill and restart rate limiter process (if separate)
kubectl exec -it <pod-name> -- kill -9 <rate_limiter_pid>
# 2. Service should auto-restart
# 3. Monitor for recovery
# Estimated time: 2 minutes
```

**Path B: Adjust Rate Limit Config**
```bash
# 1. Current limit: 2 req/sec (Shopify's requirement)
# 2. If still getting rate limited, may indicate:
#    - Multiple replicas not coordinating
#    - Solution: Implement distributed rate limiter using Redis
# 3. Temporary workaround: reduce concurrent pods
kubectl scale deployment/felix-api --replicas=2
# 4. Monitor Shopify API for recovery
# Estimated time: 5 minutes
```

**Path C: Investigate Webhook Flood**
```bash
# If Shopify is sending too many events:
1. Check webhook topic subscriptions in config
2. Verify webhook_topics in config.production.yaml
3. Unsubscribe from unnecessary topics if possible
4. Monitor event processing queue
5. Estimated time: 10 minutes
```

**Path D: Rollback**
```bash
# If issue introduced by v14.0.0 changes:
kubectl rollout undo deployment/felix-api
# Verify rate limiting returns to normal
# Estimated time: 15 minutes
```

**Decision Matrix:**
```
Error % | Sync Success | Action
1-5% | >95% | Monitor, apply Path A if persists
5-20% | 90-95% | Apply Path A or B
20-50% | <90% | Apply Path C investigation
> 50% | <70% | Apply Path D (Rollback)
```

**Post-Resolution:**
- [ ] Verify sync success rate >99%
- [ ] Confirm no 429 errors in logs
- [ ] Check Shopify webhook processing delay <10s
- [ ] Verify order data flowing to dashboard
- [ ] Log incident, note if coordination issue needs fixing

---

### Scenario 3: A/B Test Statistical Calculation Errors

**Symptoms:**
- A/B test results showing incorrect p-values
- Winner determination being wrong (e.g., declaring loser as winner)
- Statistical tester taking >2 seconds per test
- Test creation API hanging

**Investigation Steps (5-10 min):**
```bash
# 1. Check statistical tester logs
kubectl logs -l app=felix-api | grep "statistical_tester" | tail -30

# 2. Verify sample data in database
kubectl exec <db-pod> -- sqlite3 felix.db \
  "SELECT * FROM ab_test_results LIMIT 5;"

# 3. Test statistical calculation directly
python -c "
from agents.statistical_tester import StatisticalTester
tester = StatisticalTester()
result = tester.compare_variants(test_id=1)
print(result)
"

# 4. Check for NaN or infinite values
kubectl logs -l app=felix-api | grep -i "nan\|inf\|error" | grep statistical

# 5. Verify scipy library
python -c "from scipy import stats; print(stats.__version__)"
```

**Possible Root Causes:**
1. **Division by zero** → No samples in one variant
2. **Insufficient sample size** → <100 samples (too early to calculate)
3. **scipy bug or version mismatch** → Library issue
4. **Database write race condition** → Results written before complete
5. **Float precision issue** → Very small p-values causing numerical instability

**Resolution Paths:**

**Path A: Quick Fix - Skip Low-Sample Tests**
```python
# Modify statistical_tester.py
def compare_variants(self, test_id: int):
    results = self.get_test_results(test_id)
    
    # Ensure minimum samples
    if results['A']['sent'] < 100 or results['B']['sent'] < 100:
        return {
            'status': 'insufficient_samples',
            'message': 'Need at least 100 samples per variant',
            'winner': None
        }
    
    # ... rest of calculation
```
- Estimated time: 5 minutes

**Path B: Debug Sample Data**
```bash
# Check if variant assignment is working
1. Query ab_tests table for recent tests
2. Check ab_test_results for variant distribution
3. Verify assignment is 50-50 split
4. If not, variant assigner may be broken
5. Estimated time: 10 minutes
```

**Path C: Restart Service with Library Fix**
```bash
# If scipy is causing issues:
1. Update requirements.txt with explicit scipy version
2. Rebuild container
3. Redeploy
4. Estimated time: 5-10 minutes (if minor version)
```

**Path D: Rollback**
```bash
# If A/B testing framework introduced bug:
kubectl rollout undo deployment/felix-api
# Verify old A/B tests still work if any were running
# Estimated time: 15 minutes
```

**Decision Matrix:**
```
Error % | Calculation Accuracy | Action
1-5% | >95% accurate | Monitor, apply Path A if systemic
5-20% | 80-95% accurate | Apply Path B (check data)
20-50% | 50-80% accurate | Apply Path C (library fix)
> 50% | <50% accurate | Apply Path D (Rollback)
```

**Post-Resolution:**
- [ ] Verify statistical calculations are correct
- [ ] Run test with known data to confirm math
- [ ] Check p-value accuracy (compare to manual calc)
- [ ] Verify winner determination matches expectations
- [ ] Log incident, document if minimum sample size needs increase

---

### Scenario 4: Database Performance Degradation

**Symptoms:**
- Query latency spiking (from 12ms to 50ms+)
- Dashboard loading slowly
- API responses timing out
- Connection pool at capacity

**Investigation Steps (5-10 min):**
```bash
# 1. Check slow query log
kubectl exec <db-pod> -- sqlite3 felix.db \
  "SELECT * FROM sqlite_master WHERE type='index';"

# 2. Check database size
kubectl exec <db-pod> -- du -sh /var/lib/sqlite/felix.db

# 3. Check active connections
kubectl exec <db-pod> -- sqlite3 felix.db \
  "PRAGMA database_list;"

# 4. Check for lock contention
kubectl logs -l app=felix-api | grep -i "database lock\|busy" | wc -l

# 5. Check new tables for missing indexes
# Tables added in FASE 14:
# - prediction_history
# - ab_tests, ab_test_results
# - shopify_stores, shopify_orders, shopify_products, shopify_webhooks

# 6. Run VACUUM to optimize database
kubectl exec <db-pod> -- sqlite3 felix.db "VACUUM;"
```

**Possible Root Causes:**
1. **Missing indexes on new tables** → Queries full-scanning prediction_history, ab_test_results
2. **Database bloat** → Tables not vacuumed since migration
3. **Lock contention** → Multiple pods writing to same table
4. **Inefficient queries** → New code introduced N+1 queries
5. **Statistics outdated** → Query planner making wrong decisions

**Resolution Paths:**

**Path A: Add Missing Indexes**
```sql
-- Check what indexes exist
PRAGMA index_list(prediction_history);
PRAGMA index_list(ab_tests);
PRAGMA index_list(ab_test_results);

-- Add if missing:
CREATE INDEX idx_prediction_history_client_id 
  ON prediction_history(client_id);

CREATE INDEX idx_ab_tests_active 
  ON ab_tests(active, end_date);

CREATE INDEX idx_ab_test_results_test_id 
  ON ab_test_results(test_id, variant);

-- Verify and redeploy queries that were slow
```
- Estimated time: 10 minutes (including verification)

**Path B: Database Maintenance**
```bash
# 1. Run VACUUM to reclaim space
sqlite3 felix.db "VACUUM;"

# 2. Recompute statistics
sqlite3 felix.db "ANALYZE;"

# 3. Restart database service
kubectl restart statefulset/felix-db

# 4. Monitor query performance recovery
```
- Estimated time: 5 minutes

**Path C: Query Optimization**
```python
# Review slow queries and optimize
# Example: If fetching predictions with client data
# BEFORE (N+1 query):
predictions = db.query("SELECT * FROM prediction_history WHERE client_id IN (...)")
for p in predictions:
    client = db.query("SELECT * FROM clients WHERE id = ?", p.client_id)
    
# AFTER (JOIN):
predictions = db.query("""
    SELECT p.*, c.name FROM prediction_history p
    JOIN clients c ON p.client_id = c.id
    WHERE p.client_id IN (...)
""")
```
- Estimated time: 15-30 minutes

**Path D: Scale Database or Rollback**
```bash
# If performance can't be restored:
# Option 1: Increase database resources
kubectl patch statefulset felix-db -p \
  '{"spec":{"template":{"spec":{"resources":{"limits":{"memory":"2Gi"}}}}}}'

# Option 2: Rollback to v13.0.0
kubectl rollout undo deployment/felix-api
```
- Estimated time: 10 minutes

**Decision Matrix:**
```
Query Latency | API Impact | Action
10-30ms | None | Investigate but continue
30-100ms | Slight slowdown | Apply Path A
100-500ms | Noticeable slowdown | Apply Path A or C
> 500ms | User-visible delay | Apply Path A, C, or B
Timeouts | API fails | Apply Path D
```

**Post-Resolution:**
- [ ] Verify query latency back to <20ms average
- [ ] Check p95 latency <50ms
- [ ] Confirm dashboard loads in <2s
- [ ] Monitor for 30 minutes to ensure stable
- [ ] Add indexes to init_database.py for next deployment

---

### Scenario 5: Mobile Performance Issues (High Load Time)

**Symptoms:**
- Mobile dashboard loading > 3 seconds
- Charts not rendering on mobile
- Service worker not caching
- Offline mode not working

**Investigation Steps (5-10 min):**
```bash
# 1. Check mobile-specific metrics
curl -s http://felix-api:8000/metrics | grep mobile_load

# 2. Test dashboard load on mobile simulator
curl -A "Mozilla/5.0 (iPhone)" http://felix-api:8000/admin/dashboard \
  -w "Time: %{time_total}s\n" -o /dev/null

# 3. Check service worker status
# In browser console:
navigator.serviceWorker.ready.then(registration => {
  console.log(registration);
});

# 4. Check if JavaScript is bloated
# Measure bundle sizes
du -sh /var/www/static/js/dashboard.js

# 5. Check cache effectiveness
kubectl logs -l app=felix-api | grep "cache_hit\|cache_miss" | tail -20
```

**Possible Root Causes:**
1. **Service worker not registered properly** → Can't cache
2. **JavaScript bundle too large** → Too much data to download
3. **Chart.js rendering inefficiently** → Drawing too much data on mobile
4. **Images not optimized** → Large file sizes
5. **Network request waterfall** → Sequential instead of parallel
6. **Lazy loading not working** → Loading all data at once

**Resolution Paths:**

**Path A: Verify Service Worker**
```javascript
// Check if service worker is active
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service_worker.js')
        .then(registration => {
            console.log('Service worker registered:', registration);
            // Check if active
            if (registration.active) {
                console.log('Service worker is active');
            }
        })
        .catch(error => console.error('SW error:', error));
}
```
- If not registered, check:
  - Is service_worker.js file present?
  - Is HTTPS enabled? (required for service workers)
  - Any JavaScript errors in console?
- Estimated time: 5 minutes

**Path B: Optimize Charts for Mobile**
```python
# In PredictionBroadcaster or dashboard rendering
if is_mobile:
    # Reduce chart data points
    data_points = limit_chart_points(original_data, max_points=50)
    # Use simpler rendering
    chart_config['animation'] = False
    chart_config['responsive'] = True
    chart_config['maintainAspectRatio'] = True
```
- Estimated time: 10 minutes

**Path C: Image Optimization**
```bash
# Optimize all dashboard images
for img in frontend/images/*.png; do
  convert "$img" -resize "1280x720>" -quality 85 "$img"
done

# Measure improvement
du -sh frontend/images/
```
- Estimated time: 10 minutes

**Path D: Enable Lazy Loading**
```html
<!-- Add lazy loading to images and heavy components -->
<img src="chart.png" loading="lazy" />

<!-- Or use Intersection Observer for charts -->
<div data-lazy-load="chart-container">
    Chart will render when scrolled into view
</div>
```
- Estimated time: 15 minutes

**Decision Matrix:**
```
Load Time | User Impact | Action
2-3s | Acceptable | Monitor and optimize
3-5s | Noticeable lag | Apply Path A or B
5-10s | Poor UX | Apply Path B and C
> 10s | Unacceptable | Apply Path D or consider caching issue
```

**Post-Resolution:**
- [ ] Verify mobile load time <2s on 4G
- [ ] Test offline functionality works
- [ ] Check service worker caching data
- [ ] Confirm charts render smoothly
- [ ] Test on real mobile device (not just browser sim)

---

## Escalation Matrix

```
Severity | Time to Escalate | Escalation Path | Owner
---------|------------------|-----------------|-------
CRITICAL | 5 min | On-Call → Eng Lead → VP Eng | DevOps
HIGH | 15 min | On-Call → Eng Lead | Team Lead
MEDIUM | 1 hour | Eng Lead → Tech Debt | Team Lead
LOW | 24 hours | Log as task | Individual contributor
```

---

## Post-Incident Checklist

**Immediately After Incident (within 1 hour):**
- [ ] Incident resolved and verified stable
- [ ] Slack notification sent (#fase-14-deployment)
- [ ] Status page updated (if customer-facing)
- [ ] Initial summary posted (what, when, impact)

**Same Day (within 4 hours):**
- [ ] Post-mortem scheduled for within 24 hours
- [ ] Customer communication sent (if impact occurred)
- [ ] Metrics collected for analysis
- [ ] Temporary fixes documented

**Post-Mortem (within 24 hours):**
- [ ] Root cause analysis completed
- [ ] Prevention strategy defined
- [ ] Fix implemented and tested
- [ ] Timeline for fix deployment agreed
- [ ] Owner assigned for long-term improvement

**Follow-Up (within 1 week):**
- [ ] Fix deployed to production
- [ ] Monitoring added to prevent recurrence
- [ ] Team trained on new procedures (if applicable)
- [ ] Documentation updated
- [ ] Post-mortem review to verify fix effective

---

## Emergency Contacts

**On-Call Rotation:**
- Tonight (2026-10-06): [Engineer Name] @ [Phone]
- Tomorrow (2026-10-07): [Engineer Name] @ [Phone]

**Escalation:**
- Engineering Lead: [Name] @ [Phone/Email]
- VP Engineering: [Name] @ [Phone/Email]
- CEO (Critical Only): [Name] @ [Phone/Email]

**Communication Channels:**
- Slack: #fase-14-deployment
- PagerDuty: [Link to integration]
- War Room: [Zoom/Teams link if needed]

---

## Testing Incident Response (Monthly Drills)

To keep this playbook fresh, run monthly drills:

1. **Simulation:** Pretend WebSocket connections are down
2. **Checklist:** Run through investigation steps
3. **Timing:** Measure how long each step takes
4. **Review:** Document actual time vs expected time
5. **Update:** Improve procedures based on findings
6. **Repeat:** Run 4 scenarios per month

**Next Drill Schedule:**
- 2026-11-06: WebSocket Failure
- 2026-12-06: Shopify API Issue
- 2027-01-06: Database Performance
- 2027-02-06: A/B Testing Error

---

**Document Version:** 1.0  
**Last Reviewed:** 2026-10-06  
**Next Review:** 2026-10-13  
**Maintained By:** DevOps / SRE Team

