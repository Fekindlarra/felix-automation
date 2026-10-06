# FASE 15 Deployment Checklist
**WhatsApp Integration & Conversion Tracking - Production Deployment**

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Team & Resources
- [ ] Development team assigned (2-3 developers)
- [ ] Project manager assigned
- [ ] Budget approved ($30,000 dev + $500/mo Twilio)
- [ ] Timeline confirmed (6-8 weeks)
- [ ] Go-live date scheduled

### Infrastructure Setup
- [ ] Twilio Business account created
- [ ] Twilio WhatsApp sandbox configured
- [ ] WhatsApp number linked to account
- [ ] API credentials obtained
- [ ] Environment variables configured (not in git)
- [ ] HTTPS certificate valid for webhook domain
- [ ] Webhook URL publicly accessible

### Development Environment
- [ ] Python 3.11+ installed
- [ ] SQLite3 available
- [ ] Dependencies installed (twilio, httpx, python-dateutil)
- [ ] Database clone created for testing
- [ ] Feature branches created for each PASO

---

## 🔧 IMPLEMENTATION PHASES

### PHASE 1: Foundation (Weeks 1-2)

#### PASO 1: Twilio Setup (3 days)
- [ ] Twilio console access verified
- [ ] WhatsApp Business account activated
- [ ] Sandbox webhook URL configured
- [ ] Message template approved by WhatsApp
- [ ] Authentication credentials stored securely
- [ ] Rate limiting configured (80 msg/sec)
- [ ] Error handling for API failures tested

**Verification:**
```bash
# Test connection
curl -X POST https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages \
  -d "To=+1234567890" \
  -d "From=+sandbox" \
  -d "Body=Test"
```

#### PASO 2: Database Schema (2 days)
- [ ] Backup existing database created
- [ ] 3 new tables created (without downtime)
  - [ ] `whatsapp_messages`
  - [ ] `whatsapp_conversion_tracking`
  - [ ] `whatsapp_ab_tests`
- [ ] All indices created
- [ ] Foreign key constraints verified
- [ ] Database integrity check passed
- [ ] Migration rollback script created

**Verification:**
```bash
python init_database.py
sqlite3 data/pipeline.sqlite ".tables"  # Verify new tables
```

#### PASO 3: WhatsApp Message Agent (3 days)
- [ ] `agents/whatsapp_message_agent.py` created
- [ ] Message formatting working
- [ ] Twilio integration functional
- [ ] Template personalization tested
- [ ] Error handling and retries implemented
- [ ] Phone number validation working (E.164)
- [ ] Unit tests pass (8 tests)

**Verification:**
```bash
pytest agents/test_whatsapp_message_agent.py -v
# Expected: 8/8 tests pass
```

### PHASE 2: Tracking (Weeks 2-3)

#### PASO 4: Conversion Tracking System (4 days)
- [ ] `analytics/conversion_tracker.py` created
- [ ] Event logging functional
- [ ] Funnel rate calculations working
- [ ] Drop-off stage identification accurate
- [ ] Device tracking collecting data
- [ ] Query performance optimized
- [ ] Unit tests pass (9 tests)

**Verification:**
```bash
pytest analytics/test_conversion_tracker.py -v
# Expected: 9/9 tests pass
```

#### PASO 5: Webhook Handler (3 days)
- [ ] `backend/routes/whatsapp_webhooks.py` created
- [ ] Endpoints created:
  - [ ] `POST /webhooks/whatsapp/status`
  - [ ] `POST /webhooks/whatsapp/messages`
- [ ] HMAC-SHA256 signature validation working
- [ ] Event processing functional
- [ ] WebSocket broadcasting working
- [ ] Webhook logging complete
- [ ] Unit tests pass (10 tests)

**Verification:**
```bash
pytest backend/test_whatsapp_webhooks.py -v
# Expected: 10/10 tests pass

# Test webhook signature
python -c "
import hmac, hashlib
payload = 'test'
token = 'webhook_token'
sig = hmac.new(token.encode(), payload.encode(), hashlib.sha256).hexdigest()
print(f'Signature: {sig}')
"
```

### PHASE 3: Testing & Analysis (Weeks 3-4)

#### PASO 6: A/B Testing Framework (3 days)
- [ ] `agents/whatsapp_ab_tester.py` created
- [ ] Variant assignment deterministic (hash-based)
- [ ] Statistical significance calculation accurate
- [ ] Chi-square test implemented
- [ ] Winner determination automatic
- [ ] Integration with existing `statistical_tester.py` working
- [ ] Unit tests pass (7 tests)

**Verification:**
```bash
pytest agents/test_whatsapp_ab_tester.py -v
# Expected: 7/7 tests pass

# Test variant assignment
python -c "
from agents.whatsapp_ab_tester import WhatsAppABTester
tester = WhatsAppABTester()
v1 = tester.assign_variant(test_id=1, client_id=100)
v2 = tester.assign_variant(test_id=1, client_id=100)
assert v1 == v2  # Must be deterministic
print(f'Variant assignment: {v1}')
"
```

#### PASO 7: Conversion Dashboard (4 days)
- [ ] `frontend/whatsapp_dashboard.html` created
- [ ] Funnel visualization (Sankey) rendering correctly
- [ ] Metric cards displaying accurate data
- [ ] A/B test results showing statistics
- [ ] Time series chart (conversions by hour/day)
- [ ] Device performance breakdown working
- [ ] ROI calculator functional
- [ ] Responsive design verified (mobile, tablet, desktop)
- [ ] WebSocket real-time updates working
- [ ] Load time <2 seconds

**Verification:**
```bash
# Manual verification required
# Open in browser: http://localhost:8000/whatsapp/dashboard
# Verify:
# - Funnel shows 5 stages (sent, delivered, read, clicked, converted)
# - Metrics update in real-time
# - Charts render without errors
```

### PHASE 4: Integration (Weeks 4-5)

#### PASO 8: Sales Pipeline Integration (4 days)
- [ ] `agents/whatsapp_pipeline_trigger.py` created
- [ ] Triggers implemented:
  - [ ] `on_proposal_sent()` (4h delay)
  - [ ] `on_proposal_read()` (2h delay)
  - [ ] `on_proposal_clicked()` (trigger reminder)
  - [ ] `on_proposal_accepted()` (confirmation)
- [ ] Follow-up sequences working (Day 2, 4, 7)
- [ ] Pipeline updates automatic
- [ ] Message queue managing throughput
- [ ] Unit tests pass (8 tests)

**Verification:**
```bash
pytest agents/test_whatsapp_pipeline_trigger.py -v
# Expected: 8/8 tests pass
```

#### PASO 9: Comprehensive Testing (5 days)
- [ ] Unit tests: 27 tests passing
- [ ] Integration tests: 12 tests passing
- [ ] E2E tests: 8 tests passing
- [ ] Load test: 80 msg/sec sustained
- [ ] Performance benchmarks met:
  - [ ] Message send latency <2s
  - [ ] Webhook processing <200ms
  - [ ] Dashboard load <1.5s
- [ ] Database transaction consistency verified
- [ ] No memory leaks detected
- [ ] Error handling tested

**Verification:**
```bash
# Run all tests
pytest tests/ -v --tb=short

# Load test
python tests/load/test_whatsapp_80_messages_per_sec.py

# Coverage report
pytest --cov=agents --cov=analytics --cov=backend tests/
# Expected coverage: >85%
```

### PHASE 5: Optimization & Documentation (Weeks 5-6)

#### PASO 10: Performance Optimization (3 days)
- [ ] Database queries optimized (no N+1)
- [ ] Query response times <100ms
- [ ] Caching implemented for frequent queries
- [ ] WebSocket payload optimized
- [ ] Dashboard assets minified
- [ ] Image compression applied
- [ ] CSS/JS bundling verified

**Verification:**
```bash
# Query performance check
python -c "
import sqlite3, time
db = sqlite3.connect('data/pipeline.sqlite')
start = time.time()
result = db.execute('SELECT * FROM whatsapp_conversion_tracking WHERE client_id=?', (1,)).fetchall()
elapsed = (time.time() - start) * 1000
print(f'Query time: {elapsed:.1f}ms')
assert elapsed < 100  # Must be <100ms
"
```

#### PASO 11: Documentation & Training (3 days)
- [ ] FASE_15_RELEASE_NOTES.md completed
- [ ] Deployment checklist created (this file)
- [ ] API documentation updated
- [ ] Webhook integration guide created
- [ ] A/B testing user guide written
- [ ] Troubleshooting guide compiled
- [ ] Team training completed
- [ ] Run-books for operations created

---

## 🔒 SECURITY VERIFICATION

### Pre-Deployment Security Checks
- [ ] Phone numbers encrypted (Fernet AES-128)
- [ ] HMAC-SHA256 validation functional
- [ ] API tokens in environment variables (not hardcoded)
- [ ] No secrets in git history (`git log --all -S password`)
- [ ] HTTPS enforced (no http)
- [ ] Rate limiting configured (per-client)
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] CORS policy correct
- [ ] No sensitive data in logs

**Verification:**
```bash
# Check for hardcoded secrets
grep -r "api_key\|token\|secret" --include="*.py" | grep -v test | grep -v ".pyc"
# Should return: 0 results (only in config/env files)

# Verify rate limiting
python -c "from backend.ratelimiter import RateLimiter; rl = RateLimiter(80, 1); print('Rate limiter OK')"
```

---

## 📊 PERFORMANCE VALIDATION

### Performance Targets
| Metric | Target | Threshold | Status |
|--------|--------|-----------|--------|
| Message Send Latency | <2s | <5s | [ ] |
| Webhook Processing | <200ms | <500ms | [ ] |
| Dashboard Load | <1.5s | <2s | [ ] |
| Conversion Query | <100ms | <500ms | [ ] |
| Delivery Rate | >98% | >95% | [ ] |
| Read Rate | >75% | >70% | [ ] |
| Click Rate | >45% | >40% | [ ] |
| Conversion Rate | >12% | >10% | [ ] |

**Verification:**
```bash
# Run performance test suite
pytest tests/performance/ -v
```

---

## 🧪 PRODUCTION STAGING VALIDATION

### Staging Environment
- [ ] Clone production database
- [ ] Deploy code to staging
- [ ] Run full test suite on staging
- [ ] Verify all metrics
- [ ] Load test with production-like volume
- [ ] Test backup/restore procedure
- [ ] Verify monitoring alerts work
- [ ] Test rollback procedure

**Verification:**
```bash
cd /staging
python main.py  # Start staging server
# Run production validation tests
pytest tests/production_validation/ -v
```

---

## 🚀 PRODUCTION DEPLOYMENT

### Deployment Day (Friday recommended)
- [ ] Backup production database created
- [ ] Rollback procedure documented and tested
- [ ] Team on standby for 24 hours
- [ ] Deployment window scheduled (low traffic time)
- [ ] All monitoring alerts configured
- [ ] Communication plan prepared (notify team/stakeholders)

### Deployment Steps (In Order)
1. [ ] **Code Deployment** (5 min)
   ```bash
   git pull origin main
   python -m pip install -r requirements.txt
   ```

2. [ ] **Database Migration** (10 min)
   ```bash
   python init_database.py --migrate
   ```

3. [ ] **Service Restart** (2 min)
   ```bash
   systemctl restart felix-automation
   ```

4. [ ] **Verification** (10 min)
   ```bash
   # Health checks
   curl http://localhost:8000/health
   # Verify database
   sqlite3 data/pipeline.sqlite "SELECT COUNT(*) FROM whatsapp_messages"
   ```

5. [ ] **Enable Webhooks** (5 min)
   - Update Twilio console webhook URL
   - Verify webhook delivery

**Total Deployment Time:** ~30 minutes

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Immediate (0-1 hour)
- [ ] All services started successfully
- [ ] Health check endpoint responding
- [ ] Database connection working
- [ ] WebSocket connections accepting
- [ ] Webhook endpoint accessible
- [ ] No errors in logs

**Verification:**
```bash
# Health check
curl -s http://localhost:8000/health | jq .

# Log check
tail -f logs/application.log  # Should have no ERROR entries
```

### Short-term (1-24 hours)
- [ ] Real messages sending successfully
- [ ] Webhooks receiving events
- [ ] Conversion tracking recording data
- [ ] Dashboard displaying data
- [ ] No performance degradation
- [ ] Error rate <0.1%
- [ ] Average response time <1s

**Verification:**
```bash
# Monitor in real-time
python monitoring/real_time_monitor.py

# Check metrics
curl http://localhost:8000/admin/metrics
```

### 24-hour Monitoring
- [ ] All metrics within SLA
- [ ] No data loss
- [ ] Database size within expectations
- [ ] Backup completed successfully
- [ ] Team trained on operations

---

## 🔄 ROLLBACK PROCEDURE (If Needed)

### Immediate Rollback (Emergency)
1. [ ] Stop application
   ```bash
   systemctl stop felix-automation
   ```

2. [ ] Restore database backup
   ```bash
   cp backups/pipeline.sqlite.backup data/pipeline.sqlite
   ```

3. [ ] Revert code to previous version
   ```bash
   git revert HEAD
   git push origin main
   ```

4. [ ] Restart application
   ```bash
   systemctl start felix-automation
   ```

5. [ ] Verify restoration
   ```bash
   curl http://localhost:8000/health
   ```

### Post-Rollback Analysis
- [ ] Identify root cause
- [ ] Fix issue in code
- [ ] Run full test suite
- [ ] Stage fix in staging environment
- [ ] Re-attempt deployment

---

## 📞 SUPPORT CONTACTS

| Role | Name | Contact |
|------|------|---------|
| Project Lead | Felipe Rodriguez | felipe@enbuenamesa.com |
| Dev Lead | [Name] | [email] |
| Ops Lead | [Name] | [email] |
| On-call (24h) | [Name] | [email] |

---

## 📝 DEPLOYMENT SIGN-OFF

**Pre-Deployment Review:**
- [ ] All checklist items completed
- [ ] All tests passing (47/47)
- [ ] Security review passed
- [ ] Performance benchmarks met
- [ ] Team ready
- [ ] Stakeholder approval obtained

**Deployment Authorization:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| PM | Felipe Rodriguez | __________ | ______ |
| Dev Lead | | __________ | ______ |
| Ops Lead | | __________ | ______ |

---

**Checklist Created:** October 6, 2026  
**Valid Through:** November 30, 2026  
**Next Review:** Post-deployment

**Status:** ✅ READY FOR DEPLOYMENT (Upon Approval)

For questions or clarifications: felipe@enbuenamesa.com
